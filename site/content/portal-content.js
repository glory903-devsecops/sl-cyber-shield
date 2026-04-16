const reportArchive = "index.html";
const visualJourney = "journey.html";
const reportsManifest = "data/reports-manifest.json";

const homeStats = Object.freeze([
    { label: "Primary Demo", value: "GitHub Pages" },
    { label: "Story Flow", value: "Landing -> Reports" },
    { label: "Current Focus", value: "UI First" },
]);

const reportStats = Object.freeze([
    { label: "Report Set", value: "Main + Insider" },
    { label: "Story Asset", value: "6-Step Journey" },
    { label: "Delivery Mode", value: "Static HTML" },
]);

const checkpoints = Object.freeze([
    {
        title: "Safe demo baseline",
        badge: "Ready",
        badgeVariant: "safe",
        body: "Pages 랜딩을 별도 진입점으로 유지하고, 보고서 링크를 최신 산출물 기준으로 고정해 데모 공유 시점의 안정성을 높였습니다.",
    },
    {
        title: "Refactor staging lane",
        badge: "Next",
        badgeVariant: "focus",
        body: "향후 파이썬 실행 계층과 정적 사이트 계층을 더 분리해도 데모 랜딩은 독립적으로 유지되도록 구조를 나누는 방향입니다.",
    },
]);

const reportTimeline = Object.freeze([
    {
        title: "External exploit chain",
        body: "Spring4Shell 기반 외부 공격자가 초기 진입, RCE, 권한 상승, 내부 확장을 거치는 메인 시나리오입니다.",
    },
    {
        title: "Insider supply-chain path",
        body: "내부자 관점에서 자격 증명 노출과 빌드 파이프라인 확장을 보여주는 보조 시나리오입니다.",
    },
    {
        title: "Visual attack journey",
        body: "비전문가도 흐름을 따라갈 수 있도록 정찰부터 데이터 유출까지 6단계로 시각화한 내러티브 자산입니다.",
    },
]);

const architectureNotes = Object.freeze([
    {
        title: "Presentation isolation",
        copy: "랜딩/보고서 포털에서 사용하는 콘텐츠 정의와 렌더링 로직을 분리해, 이후 디자인 변경이 파일 전체 복붙으로 번지지 않도록 정리했습니다.",
        bullets: [
            "공유 콘텐츠는 모듈에 두고 각 페이지는 base path만 주입합니다.",
            "링크 경로와 카드 정보는 한 곳에서 관리합니다.",
        ],
    },
    {
        title: "Deployment-aware UI",
        copy: "GitHub Pages의 정적 배포 특성을 기준으로, 빌드 도구 없이도 404와 경로 문제를 낮출 수 있는 구조를 우선 적용했습니다.",
        bullets: [
            "루트 랜딩과 `03.FinalReport` 포털 모두 같은 스타일 시스템을 사용합니다.",
            "별도 `404.html`을 추가해 제출 링크 실패 시 복귀 경로를 제공합니다.",
        ],
    },
    {
        title: "Clean next step",
        copy: "다음 리팩토링 단계에서는 파이썬 도메인/포트/어댑터 계층과 프론트엔드 정적 프레젠테이션 계층의 책임을 더 선명하게 나누면 됩니다.",
        bullets: [
            "도메인 모델 검토와 유스케이스 분리를 별도 단계로 진행합니다.",
            "배포용 데모는 안정 브랜치 또는 배포용 폴더로 관리하는 전략을 추천합니다.",
        ],
    },
    {
        title: "Manifest-driven reports",
        copy: "정적 보고서 포털은 더 이상 최신 파일명을 코드에 하드코딩하지 않고, 빌드 시 갱신되는 manifest를 읽어 최신 HTML/PDF 번들을 노출합니다.",
        bullets: [
            "새 보고서 번들이 생기면 manifest가 함께 갱신됩니다.",
            "포털은 manifest 로드 실패 시 안전한 fallback 링크로 동작합니다.",
        ],
    },
]);

const fallbackCatalog = Object.freeze({
    main: {
        slug: "main_scenario_report_20260330_231923",
        kind: "main",
        title: "SL Cyber-Shield Main Exploit Chain",
        subtitle: "Spring4Shell 기반 메인 침투 시나리오의 최신 고정 보고서입니다.",
        generatedAt: "2026-03-30 23:19:23",
        htmlFile: "main_scenario_report_20260330_231923.html",
        jsonFile: "",
        pdfFile: "",
        hasPdf: false,
    },
    insider: {
        slug: "sub_scenario_insider_threat_20260328_184448",
        kind: "insider",
        title: "SL Cyber-Shield Insider Threat Audit",
        subtitle: "내부자 위협 및 공급망 이동 흐름의 최신 고정 보고서입니다.",
        generatedAt: "2026-03-28 18:44:48",
        htmlFile: "sub_scenario_insider_threat_20260328_184448.html",
        jsonFile: "",
        pdfFile: "",
        hasPdf: false,
    },
});

function resolveFeaturedReport(reportCatalog, kind) {
    const manifestReport =
        reportCatalog?.reports?.find((report) => report.kind === kind) ?? fallbackCatalog[kind];
    return manifestReport ?? null;
}

function formatReportDate(dateString) {
    return dateString ? dateString.replace(" ", " / ") : "Pinned";
}

function buildReports(reportBasePath, scope, reportCatalog) {
    const latestMainReport = resolveFeaturedReport(reportCatalog, "main");
    const latestInsiderReport = resolveFeaturedReport(reportCatalog, "insider");
    const shared = [
        {
            title: "Main Exploit Chain",
            description: "외부 공격자 기준의 주요 침투 시나리오와 실제 공격 체인을 기술 보고서 형식으로 정리한 메인 산출물입니다.",
            href: `${reportBasePath}${latestMainReport?.htmlFile ?? fallbackCatalog.main.htmlFile}`,
            type: "Primary Report",
            tag: "Latest",
            icon: "01",
            note: formatReportDate(latestMainReport?.generatedAt),
            pdfHref:
                latestMainReport?.hasPdf && latestMainReport?.pdfFile
                    ? `${reportBasePath}${latestMainReport.pdfFile}`
                    : "",
        },
        {
            title: "Insider Threat",
            description: "내부자 위협과 공급망 이동 관점의 보조 시나리오를 별도 관제 보고서 형태로 제공합니다.",
            href: `${reportBasePath}${latestInsiderReport?.htmlFile ?? fallbackCatalog.insider.htmlFile}`,
            type: "Secondary Report",
            tag: "Latest",
            icon: "02",
            note: formatReportDate(latestInsiderReport?.generatedAt),
            pdfHref:
                latestInsiderReport?.hasPdf && latestInsiderReport?.pdfFile
                    ? `${reportBasePath}${latestInsiderReport.pdfFile}`
                    : "",
        },
        {
            title: "Visual Journey",
            description: "공격의 흐름을 비전문가도 이해할 수 있도록 단계별 시각 스토리로 풀어낸 프레젠테이션 자산입니다.",
            href: `${reportBasePath}${visualJourney}`,
            type: "Story Layer",
            tag: "Narrative",
            icon: "03",
            note: "Static asset",
            pdfHref: "",
        },
    ];

    if (scope === "report") {
        shared.push({
            title: "Report Archive",
            description: "날짜별로 생성된 보고서 산출물을 다시 열어보며 버전별 비교에 활용할 수 있는 포털 진입점입니다.",
            href: `${reportBasePath}${reportArchive}`,
            type: "Archive",
            tag: "Portal",
            icon: "04",
            note: `${reportCatalog?.reports?.length ?? 2} tracked bundle(s)`,
            pdfHref: "",
        });
    }

    return shared;
}

export async function loadReportCatalog(reportBasePath) {
    const manifestUrl = `${reportBasePath}${reportsManifest}`;
    try {
        const response = await fetch(manifestUrl, { cache: "no-store" });
        if (!response.ok) {
            throw new Error(`Manifest request failed: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        return {
            version: 1,
            updatedAt: "",
            reports: [fallbackCatalog.main, fallbackCatalog.insider],
            fallback: true,
        };
    }
}

export function createPortalModel({ reportBasePath, homePath, scope, reportCatalog }) {
    if (!reportBasePath || !homePath || !scope) {
        throw new Error("Portal model requires reportBasePath, homePath, and scope.");
    }

    const isHome = scope === "home";
    const latestMainReport = resolveFeaturedReport(reportCatalog, "main");
    const latestInsiderReport = resolveFeaturedReport(reportCatalog, "insider");
    const trackedCount = reportCatalog?.reports?.length ?? 2;

    return {
        brand: {
            title: "SL Cyber-Shield",
            meta: "Security Simulation Portfolio",
        },
        hero: isHome
            ? {
                eyebrow: "Demo-safe front door",
                title: "Stabilize the demo first,\nthen keep refactoring.",
                lead: "제출용 링크의 첫 인상과 신뢰도를 지키기 위해, 메인 랜딩을 보고서 관문 역할에 집중시키고 최신 산출물만 안정적으로 노출하도록 구성했습니다.",
                primaryAction: {
                    label: "최신 메인 보고서 보기",
                    href: `${reportBasePath}${latestMainReport?.htmlFile ?? fallbackCatalog.main.htmlFile}`,
                },
                secondaryAction: {
                    label: "보고서 포털 열기",
                    href: `${reportBasePath}${reportArchive}`,
                },
                stats: [
                    ...homeStats.slice(0, 2),
                    { label: "Tracked Bundles", value: String(trackedCount) },
                ],
                summaryTitle: "Why this landing exists",
                summaryCopy: "이 화면은 리팩토링 중에도 데모 링크가 흔들리지 않게 해주는 안전한 진입점입니다. 보고서 링크, 시각 자료, 현재 작업 방향을 한눈에 정리해 전달력을 높이는 역할에 집중합니다. 최신 보고서 링크는 manifest를 읽어 자동으로 갱신됩니다.",
            }
            : {
                eyebrow: "Report control tower",
                title: "Report portal for\ntechnical evidence.",
                lead: "메인 데모 랜딩에서 연결되는 상세 포털입니다. 최신 보고서, 시각 여정, 보조 시나리오를 한곳에서 바로 열 수 있도록 구성했습니다.",
                primaryAction: {
                    label: "메인 데모로 돌아가기",
                    href: homePath,
                },
                secondaryAction: {
                    label: "Visual Journey 보기",
                    href: `${reportBasePath}${visualJourney}`,
                },
                stats: [
                    ...reportStats.slice(0, 2),
                    { label: "Latest Main", value: formatReportDate(latestMainReport?.generatedAt) },
                ],
                summaryTitle: "Submission-safe navigation",
                summaryCopy: "직접 공유되는 링크에서 산출물 탐색이 복잡해지지 않도록, 제출 시점에 보여줄 핵심 자료만 먼저 배치하고 확장 자료는 같은 흐름 안에서 접근하도록 구성했습니다. 최신 메인/내부자 보고서는 빌드 시 갱신되는 manifest를 기준으로 노출합니다.",
            },
        quickLink: isHome
            ? {
                label: "Report Portal",
                href: `${reportBasePath}${reportArchive}`,
            }
            : {
                label: "Home",
                href: homePath,
            },
        checkpoints,
        reports: buildReports(reportBasePath, scope, reportCatalog),
        timeline: reportTimeline,
        architectureNotes,
        footer: {
            copy: `SL Factory Innovation Team demo delivery layer. Static Pages first, deeper refactoring next. Manifest tracks ${trackedCount} bundle(s).`,
            homePath,
        },
    };
}
