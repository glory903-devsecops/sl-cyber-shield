import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { ReportDocument } from "../react/report-document.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, "../..");

function parseArgs(argv) {
  const args = {};
  for (let index = 2; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--")) {
      continue;
    }
    const key = token.slice(2);
    const value = argv[index + 1] && !argv[index + 1].startsWith("--") ? argv[index + 1] : "true";
    args[key] = value;
    if (value !== "true") {
      index += 1;
    }
  }
  return args;
}

function ensureTailwindCss() {
  const cssInput = path.join(projectRoot, "reporting/styles/input.css");
  const cssOutputDir = path.join(projectRoot, "reporting/generated");
  const cssOutput = path.join(cssOutputDir, "report.css");
  fs.mkdirSync(cssOutputDir, { recursive: true });

  const result = spawnSync(
    "npx",
    ["@tailwindcss/cli", "-i", cssInput, "-o", cssOutput, "--minify"],
    {
      cwd: projectRoot,
      encoding: "utf-8",
      stdio: "pipe",
    },
  );

  if (result.status !== 0) {
    throw new Error(result.stderr || "Tailwind build failed.");
  }

  return fs.readFileSync(cssOutput, "utf-8");
}

function renderHtml(report, css) {
  const markup = renderToStaticMarkup(React.createElement(ReportDocument, { report, css }));
  return `<!DOCTYPE html>${markup}`;
}

function detectChromeBinary() {
  const candidates = [
    process.env.REPORT_CHROME_BIN,
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "chromium",
    "chromium-browser",
  ].filter(Boolean);

  for (const candidate of candidates) {
    if (candidate.includes(path.sep)) {
      if (fs.existsSync(candidate)) {
        return candidate;
      }
      continue;
    }

    const probe = spawnSync("which", [candidate], {
      cwd: projectRoot,
      encoding: "utf-8",
      stdio: "pipe",
    });
    if (probe.status === 0) {
      return probe.stdout.trim();
    }
  }

  return null;
}

function writePdf(htmlPath, pdfPath) {
  const chromeBinary = detectChromeBinary();
  if (!chromeBinary) {
    return {
      success: false,
      message: "Google Chrome or Chromium not found; skipped PDF generation.",
    };
  }

  const result = spawnSync(
    chromeBinary,
    [
      "--headless=new",
      "--disable-gpu",
      "--no-first-run",
      "--no-default-browser-check",
      "--allow-file-access-from-files",
      "--no-pdf-header-footer",
      `--print-to-pdf=${pdfPath}`,
      pathToFileURL(htmlPath).href,
    ],
    {
      cwd: projectRoot,
      encoding: "utf-8",
      stdio: "pipe",
    },
  );

  if (result.status !== 0) {
    return {
      success: false,
      message: result.stderr || result.stdout || `Chrome headless failed to export PDF (exit: ${result.status}).`,
    };
  }

  return {
    success: true,
    message: "PDF generated successfully.",
  };
}

function main() {
  const args = parseArgs(process.argv);
  const inputPath = args.input ? path.resolve(projectRoot, args.input) : null;
  const outputDir = args["output-dir"]
    ? path.resolve(projectRoot, args["output-dir"])
    : path.join(projectRoot, "03.FinalReport");

  if (!inputPath) {
    throw new Error("Missing required --input argument.");
  }

  const raw = fs.readFileSync(inputPath, "utf-8");
  const report = JSON.parse(raw);
  const css = ensureTailwindCss();

  fs.mkdirSync(outputDir, { recursive: true });

  const stem = report.slug || path.basename(inputPath, path.extname(inputPath));
  const htmlPath = path.join(outputDir, `${stem}.html`);
  const pdfPath = path.join(outputDir, `${stem}.pdf`);

  fs.writeFileSync(htmlPath, renderHtml(report, css), "utf-8");

  const pdfResult = writePdf(htmlPath, pdfPath);

  console.log(`[report] html=${htmlPath}`);
  console.log(`[report] json=${inputPath}`);
  if (pdfResult.success) {
    console.log(`[report] pdf=${pdfPath}`);
  } else {
    console.warn(`[report] pdf-skipped=${pdfResult.message}`);
  }
}

try {
  main();
} catch (error) {
  console.error(`[report] build failed: ${error.message}`);
  process.exit(1);
}
