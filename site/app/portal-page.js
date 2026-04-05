import { createPortalModel, loadReportCatalog } from "../content/portal-content.js";

function renderStats(stats) {
    return stats
        .map(
            (stat) => `
                <article class="stat-card">
                    <div class="stat-card__label">${stat.label}</div>
                    <div class="stat-card__value">${stat.value}</div>
                </article>
            `,
        )
        .join("");
}

function renderCheckpoints(checkpoints) {
    return checkpoints
        .map(
            (item) => `
                <li class="status-card">
                    <div class="status-card__title">
                        <span>${item.title}</span>
                        <span class="badge badge--${item.badgeVariant}">${item.badge}</span>
                    </div>
                    <p class="status-card__body">${item.body}</p>
                </li>
            `,
        )
        .join("");
}

function renderReports(reports) {
    return reports
        .map(
            (report) => `
                <a class="report-card" href="${report.href}" target="_blank" rel="noopener noreferrer">
                    <div class="report-card__meta">
                        <span class="report-card__icon">${report.icon}</span>
                        <span class="badge badge--focus">${report.tag}</span>
                    </div>
                    <h3 class="report-card__title">${report.title}</h3>
                    <p class="report-card__desc">${report.description}</p>
                    <div class="report-card__foot">
                        <span>${report.type}</span>
                        <span>${report.note ?? "Open"}</span>
                    </div>
                    ${
                        report.pdfHref
                            ? `<div class="report-card__foot"><span>PDF</span><span>${report.pdfHref.split("/").pop()}</span></div>`
                            : ""
                    }
                </a>
            `,
        )
        .join("");
}

function renderTimeline(items) {
    return items
        .map(
            (item, index) => `
                <article class="timeline-card">
                    <div class="timeline-card__title">
                        <span>0${index + 1}</span>
                        <span class="badge badge--focus">Scenario</span>
                    </div>
                    <h3 class="surface-card__title">${item.title}</h3>
                    <p class="timeline-card__body">${item.body}</p>
                </article>
            `,
        )
        .join("");
}

function renderArchitectureNotes(items) {
    return items
        .map(
            (item) => `
                <article class="surface-card">
                    <h3 class="surface-card__title">${item.title}</h3>
                    <p class="surface-card__copy">${item.copy}</p>
                    <ul class="surface-card__list">
                        ${item.bullets.map((bullet) => `<li>${bullet}</li>`).join("")}
                    </ul>
                </article>
            `,
        )
        .join("");
}

function fillText(id, value) {
    const node = document.getElementById(id);
    if (node) {
        node.textContent = value;
    }
}

function fillHtml(id, value) {
    const node = document.getElementById(id);
    if (node) {
        node.innerHTML = value;
    }
}

function setLink(id, link) {
    const node = document.getElementById(id);
    if (node) {
        node.href = link.href;
        node.textContent = link.label;
    }
}

function renderPage(model) {
    fillText("brand-title", model.brand.title);
    fillText("brand-meta", model.brand.meta);
    setLink("top-link", model.quickLink);

    fillText("hero-eyebrow", model.hero.eyebrow);
    fillText("hero-title", model.hero.title);
    fillText("hero-lead", model.hero.lead);
    setLink("hero-primary", model.hero.primaryAction);
    setLink("hero-secondary", model.hero.secondaryAction);
    fillHtml("hero-stats", renderStats(model.hero.stats));

    fillText("summary-title", model.hero.summaryTitle);
    fillText("summary-copy", model.hero.summaryCopy);
    fillHtml("checkpoint-list", renderCheckpoints(model.checkpoints));

    fillHtml("reports-grid", renderReports(model.reports));
    fillHtml("timeline-grid", renderTimeline(model.timeline));
    fillHtml("architecture-grid", renderArchitectureNotes(model.architectureNotes));

    fillText("footer-copy", model.footer.copy);
    const footerLink = document.getElementById("footer-link");
    if (footerLink) {
        footerLink.href = model.footer.homePath;
    }
}

async function bootstrap() {
    const page = document.body.dataset.page ?? "home";
    const reportBasePath = document.body.dataset.reportBasePath ?? "./03.FinalReport/";
    const homePath = document.body.dataset.homePath ?? "./";
    const reportCatalog = await loadReportCatalog(reportBasePath);

    renderPage(
        createPortalModel({
            reportBasePath,
            homePath,
            scope: page,
            reportCatalog,
        }),
    );
}

bootstrap();
