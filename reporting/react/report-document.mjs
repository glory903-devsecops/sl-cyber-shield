import React from "react";

const h = React.createElement;

function renderItems(items = [], renderer) {
  return items.map((item, index) => renderer(item, index));
}

function toneClasses(status) {
  const styles = {
    success: "border-emerald-400/30 bg-emerald-400/10 text-emerald-200",
    blocked: "border-rose-400/30 bg-rose-400/10 text-rose-200",
    incomplete: "border-amber-300/30 bg-amber-300/10 text-amber-100",
    warning: "border-amber-300/30 bg-amber-300/10 text-amber-100",
  };
  return styles[status] ?? "border-cyan-300/30 bg-cyan-300/10 text-cyan-100";
}

function severityClasses(severity) {
  const styles = {
    critical: "border-rose-400/35 bg-rose-500/12 text-rose-100",
    high: "border-orange-300/35 bg-orange-400/12 text-orange-100",
    medium: "border-cyan-300/35 bg-cyan-300/12 text-cyan-100",
    low: "border-emerald-300/35 bg-emerald-300/12 text-emerald-100",
  };
  return styles[(severity ?? "").toLowerCase()] ?? styles.medium;
}

function StatCard(item, index) {
  return h(
    "article",
    {
      key: `${item.label}-${index}`,
      className:
        "rounded-[1.4rem] border border-white/10 bg-white/[0.04] px-4 py-4 shadow-[0_16px_50px_rgba(2,6,23,0.25)]",
    },
    [
      h(
        "div",
        {
          key: "label",
          className: "text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-slate-400",
        },
        item.label,
      ),
      h(
        "div",
        {
          key: "value",
          className: "mt-3 text-[1rem] font-semibold leading-6 text-slate-50",
        },
        item.value,
      ),
    ],
  );
}

function ArtifactCard(item, index) {
  const content = [
    h(
      "div",
      {
        key: "label",
        className: "text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-cyan-200/80",
      },
      item.label,
    ),
    h(
      "div",
      {
        key: "value",
        className: "mt-4 text-base font-semibold leading-7 text-slate-50",
      },
      item.value,
    ),
  ];

  if (item.href) {
    return h(
      "a",
      {
        key: `${item.label}-${index}`,
        href: item.href,
        className:
          "block rounded-[1.5rem] border border-white/10 bg-[linear-gradient(180deg,rgba(34,211,238,0.10),rgba(15,23,42,0.55))] px-5 py-5 no-underline transition duration-200 hover:-translate-y-0.5",
      },
      content,
    );
  }

  return h(
    "article",
    {
      key: `${item.label}-${index}`,
      className:
        "rounded-[1.5rem] border border-white/10 bg-[linear-gradient(180deg,rgba(34,211,238,0.10),rgba(15,23,42,0.55))] px-5 py-5",
    },
    content,
  );
}

function EvidenceBlock(section) {
  const evidence = section.evidence ?? {};
  const kind = evidence.kind ?? "text";

  if (kind === "html") {
    return h("div", {
      className:
        "rounded-[1.2rem] border border-white/8 bg-slate-950/70 px-4 py-4 text-sm leading-7 text-slate-200",
      dangerouslySetInnerHTML: { __html: evidence.content ?? "" },
    });
  }

  if (kind === "list") {
    return h(
      "ul",
      {
        className:
          "grid gap-3 rounded-[1.2rem] border border-white/8 bg-slate-950/70 px-5 py-5 text-sm leading-7 text-slate-200",
      },
      renderItems(evidence.items ?? [], (item, index) =>
        h(
          "li",
          {
            key: `${section.id}-item-${index}`,
            className: "list-none rounded-2xl border border-white/6 bg-white/[0.03] px-4 py-3",
          },
          item,
        ),
      ),
    );
  }

  return h(
    "pre",
    {
      className:
        "overflow-x-auto rounded-[1.2rem] border border-cyan-400/12 bg-slate-950/80 px-4 py-4 text-[13px] leading-6 text-cyan-100 whitespace-pre-wrap",
    },
    evidence.content ?? "",
  );
}

function SectionCard(section, index) {
  const status = (section.status ?? "success").toLowerCase();
  const severity = (section.severity ?? "medium").toLowerCase();

  return h(
    "section",
    {
      key: section.id ?? `section-${index}`,
      className:
        "rounded-[1.7rem] border border-white/10 bg-white/[0.035] p-6 shadow-[0_20px_70px_rgba(2,6,23,0.28)] print:break-inside-avoid",
    },
    [
      h(
        "div",
        {
          key: "header",
          className: "flex flex-wrap items-start justify-between gap-4",
        },
        [
          h(
            "div",
            {
              key: "title-wrap",
              className: "max-w-3xl",
            },
            [
              h(
                "div",
                {
                  key: "step",
                  className: "text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-slate-400",
                },
                section.step ?? `Step ${index + 1}`,
              ),
              h(
                "h3",
                {
                  key: "title",
                  className: "mt-3 text-[1.45rem] font-semibold tracking-[-0.03em] text-white",
                },
                section.title,
              ),
              h(
                "p",
                {
                  key: "desc",
                  className: "mt-3 max-w-3xl text-[0.97rem] leading-7 text-slate-300",
                },
                section.description,
              ),
            ],
          ),
          h(
            "div",
            {
              key: "chips",
              className: "flex flex-wrap items-center gap-2",
            },
            [
              h(
                "span",
                {
                  key: "status",
                  className: `rounded-full border px-3 py-1 text-[0.72rem] font-semibold uppercase tracking-[0.18em] ${toneClasses(status)}`,
                },
                status,
              ),
              h(
                "span",
                {
                  key: "severity",
                  className: `rounded-full border px-3 py-1 text-[0.72rem] font-semibold uppercase tracking-[0.18em] ${severityClasses(severity)}`,
                },
                severity,
              ),
            ],
          ),
        ],
      ),
      h(
        "div",
        {
          key: "evidence-wrap",
          className: "mt-5",
        },
        [
          h(
            "div",
            {
              key: "evidence-label",
              className: "mb-3 text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-slate-500",
            },
            "Forensic Evidence",
          ),
          h(EvidenceBlock, { section, key: "evidence" }),
        ],
      ),
    ],
  );
}

export function ReportDocument({ report, css }) {
  return h("html", { lang: "ko" }, [
    h("head", { key: "head" }, [
      h("meta", { key: "charset", charSet: "UTF-8" }),
      h("meta", {
        key: "viewport",
        name: "viewport",
        content: "width=device-width, initial-scale=1.0",
      }),
      h("title", { key: "title" }, report.meta?.title ?? "SL Cyber-Shield Report"),
      h("style", {
        key: "style",
        dangerouslySetInnerHTML: { __html: css },
      }),
    ]),
    h(
      "body",
      {
        key: "body",
        className:
          "min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.16),transparent_32%),radial-gradient(circle_at_80%_18%,rgba(251,191,36,0.18),transparent_24%),linear-gradient(180deg,#020617_0%,#0f172a_50%,#020617_100%)] text-slate-100 print:bg-white print:text-slate-900",
      },
      [
        h(
          "main",
          {
            key: "main",
            className: "mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-8 px-4 py-8 md:px-8 xl:px-10",
          },
          [
            h(
              "section",
              {
                key: "hero",
                className:
                  "grid gap-6 lg:grid-cols-[minmax(0,1.55fr)_minmax(280px,0.9fr)]",
              },
              [
                h(
                  "article",
                  {
                    key: "hero-main",
                    className:
                      "overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(180deg,rgba(15,23,42,0.72),rgba(15,23,42,0.92))] p-7 shadow-[0_28px_90px_rgba(2,6,23,0.38)]",
                  },
                  [
                    h(
                      "div",
                      {
                        key: "hero-badge",
                        className:
                          "inline-flex rounded-full border border-cyan-300/25 bg-cyan-300/10 px-4 py-2 text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-cyan-100",
                      },
                      report.meta?.badge ?? "Static report bundle",
                    ),
                    h(
                      "h1",
                      {
                        key: "hero-title",
                        className:
                          "mt-5 max-w-4xl text-[2.6rem] font-semibold leading-[1.02] tracking-[-0.05em] text-white md:text-[4rem]",
                      },
                      report.meta?.title ?? "SL Cyber-Shield Report",
                    ),
                    h(
                      "p",
                      {
                        key: "hero-subtitle",
                        className: "mt-5 max-w-3xl text-[1.04rem] leading-8 text-slate-300",
                      },
                      report.meta?.subtitle ?? "",
                    ),
                    h(
                      "div",
                      {
                        key: "hero-summary",
                        className: "mt-7 rounded-[1.7rem] border border-white/10 bg-white/[0.03] p-5",
                      },
                      [
                        h(
                          "div",
                          {
                            key: "hero-summary-label",
                            className: "text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-slate-400",
                          },
                          "Executive Summary",
                        ),
                        h(
                          "p",
                          {
                            key: "hero-summary-copy",
                            className: "mt-4 text-[1rem] leading-8 text-slate-200",
                          },
                          report.summary?.overview ?? "",
                        ),
                      ],
                    ),
                    h(
                      "div",
                      {
                        key: "hero-stats",
                        className: "mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-4",
                      },
                      renderItems(report.summary?.items ?? [], StatCard),
                    ),
                  ],
                ),
                h(
                  "aside",
                  {
                    key: "hero-side",
                    className:
                      "grid gap-5 rounded-[2rem] border border-white/10 bg-[linear-gradient(180deg,rgba(251,191,36,0.10),rgba(15,23,42,0.92))] p-6 shadow-[0_28px_90px_rgba(2,6,23,0.32)]",
                  },
                  [
                    h(
                      "div",
                      {
                        key: "classification-label",
                        className: "text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-amber-100/80",
                      },
                      "Delivery Control",
                    ),
                    h(
                      "h2",
                      {
                        key: "classification-title",
                        className: "text-[1.5rem] font-semibold tracking-[-0.03em] text-white",
                      },
                      report.meta?.classification ?? "Built artifact",
                    ),
                    h(
                      "div",
                      {
                        key: "generated-wrap",
                        className: "rounded-[1.5rem] border border-white/10 bg-slate-950/55 px-5 py-5",
                      },
                      [
                        h(
                          "div",
                          {
                            key: "generated-label",
                            className: "text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-slate-400",
                          },
                          "Generated At",
                        ),
                        h(
                          "div",
                          {
                            key: "generated-value",
                            className: "mt-3 text-lg font-semibold text-slate-50",
                          },
                          report.meta?.generatedAt ?? "",
                        ),
                      ],
                    ),
                    h(
                      "div",
                      {
                        key: "delivery-list",
                        className: "grid gap-3",
                      },
                      [
                        "JSON as source of truth",
                        "React static export for HTML",
                        "PDF snapshot for submission archive",
                      ].map((item, index) =>
                        h(
                          "div",
                          {
                            key: `delivery-${index}`,
                            className:
                              "rounded-[1.15rem] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm leading-6 text-slate-200",
                          },
                          item,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
            h(
              "section",
              {
                key: "artifacts",
                className: "grid gap-4 md:grid-cols-3",
              },
              renderItems(report.artifacts ?? [], ArtifactCard),
            ),
            h(
              "section",
              {
                key: "timeline",
                className: "grid gap-5",
              },
              [
                h(
                  "div",
                  {
                    key: "timeline-header",
                    className: "flex flex-wrap items-end justify-between gap-4",
                  },
                  [
                    h(
                      "div",
                      { key: "timeline-copy" },
                      [
                        h(
                          "div",
                          {
                            key: "timeline-eyebrow",
                            className: "text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-cyan-200/80",
                          },
                          "Structured Timeline",
                        ),
                        h(
                          "h2",
                          {
                            key: "timeline-title",
                            className: "mt-3 text-[2rem] font-semibold tracking-[-0.04em] text-white",
                          },
                          "Scenario evidence rendered from structured data",
                        ),
                      ],
                    ),
                  ],
                ),
                ...renderItems(report.sections ?? [], SectionCard),
              ],
            ),
            h(
              "footer",
              {
                key: "footer",
                className:
                  "mt-auto rounded-[1.8rem] border border-white/10 bg-white/[0.03] px-6 py-5 text-sm leading-7 text-slate-400",
              },
              [
                h("p", { key: "footer-body" }, report.footer?.body ?? ""),
                h(
                  "p",
                  {
                    key: "footer-note",
                    className: "mt-2 text-slate-500",
                  },
                  report.footer?.note ?? "",
                ),
              ],
            ),
          ],
        ),
      ],
    ),
  ]);
}
