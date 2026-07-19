// Render a feature's properties as popup HTML. Pure, so unit-testable.

const MAX_ROWS = 12;

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatValue(value: unknown): string {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value.toLocaleString("en-CA");
  }
  return String(value);
}

function labelFor(key: string): string {
  return key.replace(/_/g, " ");
}

/**
 * Build the HTML for a feature popup: a small key/value table of the
 * feature's properties, skipping empty values, the rendering-only color
 * field, and the attribution field (shown once as a footer instead).
 */
export function popupHtml(properties: Record<string, unknown>): string {
  const rows: string[] = [];
  for (const [key, value] of Object.entries(properties)) {
    if (key === "source" || key === "color") continue;
    if (value === null || value === undefined || value === "") continue;
    if (rows.length >= MAX_ROWS) break;
    rows.push(
      `<tr><th>${escapeHtml(labelFor(key))}</th><td>${escapeHtml(formatValue(value))}</td></tr>`,
    );
  }
  const source = properties.source;
  const footer =
    typeof source === "string" && source
      ? `<div class="popup-source">${escapeHtml(source)}</div>`
      : "";
  return `<table class="popup-table"><tbody>${rows.join("")}</tbody></table>${footer}`;
}
