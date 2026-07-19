// Render a feature's properties as popup HTML. Pure, so unit-testable.

const MAX_ROWS = 12;

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function isHttpUrl(value: unknown): value is string {
  return typeof value === "string" && /^https?:\/\//i.test(value.trim());
}

function formatValue(value: unknown): string {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value.toLocaleString("en-CA");
  }
  return String(value);
}

/**
 * Render a URL as a "Open link" button that opens the target in a new tab,
 * instead of printing the raw (often overflowing) URL text.
 */
function renderUrlCell(value: string): string {
  const href = escapeHtml(value.trim());
  return `<a class="popup-link" href="${href}" target="_blank" rel="noopener noreferrer">Open link</a>`;
}

// Friendlier labels for specific property keys; everything else just has its
// underscores turned into spaces.
const LABEL_OVERRIDES: Record<string, string> = {
  url: "Source",
};

function labelFor(key: string): string {
  return LABEL_OVERRIDES[key] ?? key.replace(/_/g, " ");
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
    const cell = isHttpUrl(value)
      ? renderUrlCell(value)
      : escapeHtml(formatValue(value));
    rows.push(`<tr><th>${escapeHtml(labelFor(key))}</th><td>${cell}</td></tr>`);
  }
  const source = properties.source;
  const footer =
    typeof source === "string" && source
      ? `<div class="popup-source">${escapeHtml(source)}</div>`
      : "";
  return `<table class="popup-table"><tbody>${rows.join("")}</tbody></table>${footer}`;
}
