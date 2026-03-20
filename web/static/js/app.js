/**
 * app.js — Global state + orchestration
 */

import * as editor from './editor.js';
import { setPreviewHtml, schedulePreviewUpdate } from './preview.js';
import { renderAtsScore } from './ats.js';

// ── Global state ──────────────────────────────────────────────────────────────
let _state = {
  replacements: null,
  template: null,
  llmResponse: null,
  atsScore: null,
};

// ── Boot ──────────────────────────────────────────────────────────────────────
async function boot() {
  _initEditListener();
  await Promise.all([loadRoles(), loadTemplates()]);
}

async function loadRoles() {
  try {
    const res = await fetch('/api/roles');
    const roles = await res.json();
    const sel = document.getElementById('role-select');
    sel.innerHTML = roles.map(r => `<option value="${r.key}">${r.label}</option>`).join('');
  } catch (e) {
    console.error('Failed to load roles:', e);
  }
}

export async function loadTemplates() {
  try {
    const res = await fetch('/api/templates');
    const list = await res.json();
    const sel = document.getElementById('template-select');
    sel.innerHTML = list.map(t => `<option value="${t.id}">${t.name}</option>`).join('');

    if (list.length > 0) {
      const current = _state.template?.id || list[0].id;
      await selectTemplate(current);
    }
  } catch (e) {
    console.error('Failed to load templates:', e);
  }
}

async function selectTemplate(id) {
  try {
    const res = await fetch(`/api/templates/${id}`);
    if (!res.ok) return;
    const tmpl = await res.json();
    _state.template = tmpl;
    editor.init(tmpl, onTemplateChange);
    document.getElementById('template-select').value = id;
    if (_state.replacements) _schedulePreview();
  } catch (e) {
    console.error('Failed to load template:', e);
  }
}

// ── Generate ──────────────────────────────────────────────────────────────────
export async function generate() {
  const jd = document.getElementById('jd-textarea').value.trim();
  if (!jd) { showError('Please paste a job description.'); return; }

  const role = document.getElementById('role-select').value;
  const provider = document.getElementById('provider-select').value;
  const dryRun = document.getElementById('dry-run-check').checked;
  const templateId = _state.template?.id || 'default';

  clearError();
  setLoading(true);

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_description: jd, role, provider, dry_run: dryRun, template_id: templateId }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || res.statusText);
    }

    const data = await res.json();
    _state.replacements = data.replacements;
    _state.llmResponse  = data.llm_response;
    _state.atsScore     = data.ats_score;

    setPreviewHtml(data.preview_html);
    renderAtsScore(data.ats_score);
    enableExports(true);
    if (data.cover_letter) {
      document.getElementById('cover-letter-textarea').value = data.cover_letter;
    }
  } catch (e) {
    showError(e.message);
  } finally {
    setLoading(false);
  }
}

// ── Inline edit (postMessage from iframe) ────────────────────────────────────
function _initEditListener() {
  window.addEventListener('message', (e) => {
    if (!e.data || e.data.type !== 'cv-edit') return;
    if (!_state.replacements) return;

    const { key, idx, value } = e.data;

    if (idx !== null && idx !== undefined && Array.isArray(_state.replacements[key])) {
      // List field (bullets, skills) — clone array to avoid mutation issues
      const arr = [..._state.replacements[key]];
      arr[idx] = value;
      _state.replacements[key] = arr;
    } else {
      _state.replacements[key] = value;
    }
    // Do NOT re-render — the edit is already visible in the iframe.
    // The updated replacements will be used on the next export or template change.
  });
}

// ── Template change callback (from editor) ────────────────────────────────────
function onTemplateChange(template) {
  _state.template = template;
  if (_state.replacements) _schedulePreview();
}

function _schedulePreview() {
  schedulePreviewUpdate(async () => {
    if (!_state.replacements || !_state.template) return null;
    const res = await fetch('/api/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ replacements: _state.replacements, template: _state.template }),
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data.preview_html;
  });
}

// ── Export ────────────────────────────────────────────────────────────────────
export async function downloadPdf() {
  if (!_state.replacements || !_state.template) return;
  const base = _state.template.output_filename || 'cv';
  await _download('/api/export/pdf', `${base}.pdf`);
}

export async function downloadDocx() {
  if (!_state.replacements || !_state.template) return;
  const base = _state.template.output_filename || 'cv';
  await _download('/api/export/docx', `${base}.docx`);
}

async function _download(url, filename) {
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ replacements: _state.replacements, template: _state.template }),
    });
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail); }
    const blob = await res.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
  } catch (e) {
    showError(`Export failed: ${e.message}`);
  }
}

// ── Template selector change ──────────────────────────────────────────────────
document.getElementById('template-select').addEventListener('change', e => {
  selectTemplate(e.target.value);
});

// ── UI helpers ────────────────────────────────────────────────────────────────
function setLoading(on) {
  document.getElementById('loading-overlay').classList.toggle('hidden', !on);
  document.getElementById('btn-generate').disabled = on;
}

function enableExports(on) {
  document.getElementById('btn-pdf').disabled = !on;
  document.getElementById('btn-docx').disabled = !on;
}

function showError(msg) {
  const el = document.getElementById('error-box');
  el.textContent = msg;
  el.classList.remove('hidden');
}

function clearError() {
  const el = document.getElementById('error-box');
  el.textContent = '';
  el.classList.add('hidden');
}

// ── Cover Letter ──────────────────────────────────────────────────────────────
export async function generateCoverLetter() {
  const jd = document.getElementById('jd-textarea').value.trim();
  if (!jd) { showError('Paste a job description first.'); return; }

  const role = document.getElementById('role-select').value;
  const provider = document.getElementById('provider-select').value;

  const loadingEl = document.getElementById('cover-letter-loading');
  const btn = document.getElementById('btn-cover-letter');
  loadingEl.classList.remove('hidden');
  btn.disabled = true;

  try {
    const res = await fetch('/api/cover-letter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_description: jd, role, provider }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || res.statusText);
    }
    const data = await res.json();
    document.getElementById('cover-letter-textarea').value = data.cover_letter;
  } catch (e) {
    showError(`Cover letter failed: ${e.message}`);
  } finally {
    loadingEl.classList.add('hidden');
    btn.disabled = false;
  }
}

export async function copyCoverLetter() {
  const text = document.getElementById('cover-letter-textarea').value;
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    const btn = document.querySelector('.cover-letter-actions .btn-outline');
    const orig = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(() => { btn.textContent = orig; }, 1500);
  } catch {
    showError('Could not copy to clipboard.');
  }
}

// ── Expose to HTML inline handlers ───────────────────────────────────────────
window.app = { generate, downloadPdf, downloadDocx, loadTemplates, generateCoverLetter, copyCoverLetter };

// ── Start ─────────────────────────────────────────────────────────────────────
boot();
