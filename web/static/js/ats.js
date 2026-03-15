/**
 * ats.js — ATS score display helpers
 */

export function renderAtsScore(atsData) {
  const panel = document.getElementById('ats-panel');
  if (!atsData) { panel.classList.add('hidden'); return; }

  panel.classList.remove('hidden');

  const matchedEl = document.getElementById('ats-matched');
  const missingEl = document.getElementById('ats-missing');
  matchedEl.innerHTML = (atsData.matched_keywords || []).slice(0, 20)
    .map(k => `<span class="kw-tag kw-tag-matched">${k}</span>`).join('');
  missingEl.innerHTML = (atsData.missing_keywords || []).slice(0, 15)
    .map(k => `<span class="kw-tag kw-tag-missing">${k}</span>`).join('');
}
