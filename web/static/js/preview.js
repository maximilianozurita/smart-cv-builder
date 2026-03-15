/**
 * preview.js — iframe preview with 300ms debounce
 */

let _debounceTimer = null;
const DEBOUNCE_MS = 300;

export function setPreviewHtml(html) {
  const frame = document.getElementById('preview-frame');
  frame.srcdoc = html;
}

export function schedulePreviewUpdate(getHtmlFn) {
  clearTimeout(_debounceTimer);
  _debounceTimer = setTimeout(async () => {
    try {
      const html = await getHtmlFn();
      if (html) setPreviewHtml(html);
    } catch (e) {
      console.warn('Preview update failed:', e);
    }
  }, DEBOUNCE_MS);
}
