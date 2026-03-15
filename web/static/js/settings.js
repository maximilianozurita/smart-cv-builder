/**
 * settings.js — Data editor modal (candidate_data.json, roles.json, cv_template.docx)
 */

let _activeTab = 'candidate';

export function openSettings(tab) {
  if (tab) _activeTab = tab;
  document.getElementById('settings-modal').classList.remove('hidden');
  _switchTab(_activeTab);
}

export function closeSettings() {
  document.getElementById('settings-modal').classList.add('hidden');
}

export function switchTab(tab) {
  _activeTab = tab;
  _switchTab(tab);
}

async function _switchTab(tab) {
  // Update tab buttons
  document.querySelectorAll('.settings-tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tab);
  });
  // Show/hide panes
  document.querySelectorAll('.settings-pane').forEach(pane => {
    pane.classList.toggle('hidden', pane.dataset.pane !== tab);
  });

  if (tab === 'candidate') await _loadCandidate();
  else if (tab === 'roles') await _loadRoles();
  else if (tab === 'docx') await _loadDocxInfo();
}

// ── Candidate Data ─────────────────────────────────────────────────────────────
async function _loadCandidate() {
  try {
    const res = await fetch('/api/candidate-data');
    const data = await res.json();
    document.getElementById('candidate-editor').value = JSON.stringify(data, null, 2);
    _setStatus('candidate-status', '');
  } catch (e) {
    _setStatus('candidate-status', 'Load failed: ' + e.message, true);
  }
}

export async function saveCandidate() {
  const raw = document.getElementById('candidate-editor').value;
  try {
    const data = JSON.parse(raw);
    const res = await fetch('/api/candidate-data', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(await res.text());
    _setStatus('candidate-status', 'Saved.');
  } catch (e) {
    _setStatus('candidate-status', 'Error: ' + e.message, true);
  }
}

export async function reloadCandidate() {
  await _loadCandidate();
  _setStatus('candidate-status', 'Reloaded from disk.');
}

// ── Roles ──────────────────────────────────────────────────────────────────────
async function _loadRoles() {
  try {
    const res = await fetch('/api/roles-data');
    const data = await res.json();
    document.getElementById('roles-editor').value = JSON.stringify(data, null, 2);
    _setStatus('roles-status', '');
  } catch (e) {
    _setStatus('roles-status', 'Load failed: ' + e.message, true);
  }
}

export async function saveRoles() {
  const raw = document.getElementById('roles-editor').value;
  try {
    const data = JSON.parse(raw);
    const res = await fetch('/api/roles-data', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(await res.text());
    _setStatus('roles-status', 'Saved. Reload the page to refresh the roles dropdown.');
  } catch (e) {
    _setStatus('roles-status', 'Error: ' + e.message, true);
  }
}

export async function reloadRoles() {
  await _loadRoles();
  _setStatus('roles-status', 'Reloaded from disk.');
}

// ── DOCX Template ──────────────────────────────────────────────────────────────
async function _loadDocxInfo() {
  try {
    const res = await fetch('/api/docx-template/info');
    const info = await res.json();
    const el = document.getElementById('docx-current-info');
    if (info.exists) {
      el.textContent = `Current: ${info.name} (${info.size_kb} KB)`;
    } else {
      el.textContent = 'No template found at templates/cv_template.docx';
    }
    _setStatus('docx-status', '');
  } catch (e) {
    _setStatus('docx-status', 'Load failed: ' + e.message, true);
  }
}

export async function uploadDocx() {
  const input = document.getElementById('docx-file-input');
  const file = input.files[0];
  if (!file) return;
  const form = new FormData();
  form.append('file', file);
  try {
    const res = await fetch('/api/docx-template', { method: 'POST', body: form });
    if (!res.ok) throw new Error((await res.json()).detail);
    const info = await res.json();
    document.getElementById('docx-current-info').textContent =
      `Current: ${info.name} (${info.size_kb} KB)`;
    _setStatus('docx-status', 'Template uploaded successfully.');
    input.value = '';
  } catch (e) {
    _setStatus('docx-status', 'Upload failed: ' + e.message, true);
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────────
function _setStatus(id, msg, isError = false) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.className = 'settings-status' + (isError ? ' settings-status-error' : '');
}

// Close on backdrop click
document.getElementById('settings-modal').addEventListener('click', e => {
  if (e.target === document.getElementById('settings-modal')) closeSettings();
});

window.settings = { openSettings, closeSettings, switchTab, saveCandidate, reloadCandidate, saveRoles, reloadRoles, uploadDocx };
