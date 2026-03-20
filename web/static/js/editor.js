/**
 * editor.js — Template editor: sections list (drag-to-reorder) + page config
 */

import { schedulePreviewUpdate } from './preview.js';

// ── State (shared via import in app.js) ───────────────────────────────────────
let _template = null;
let _onChangeCallback = null;

export function init(template, onChangeFn) {
  _template = template;
  _onChangeCallback = onChangeFn;
  _syncPageConfigUI();
  _renderSectionsList();
}

export function getTemplate() {
  return _template;
}

export function setTemplate(template) {
  _template = template;
  _syncPageConfigUI();
  _renderSectionsList();
}

// ── Page config ───────────────────────────────────────────────────────────────
function _syncPageConfigUI() {
  if (!_template) return;
  const p = _template.page;
  _setVal('template-name-input', _template.name ?? '');
  _setVal('cfg-output-filename', _template.output_filename ?? 'cv');
  _setVal('cfg-font', p.font_family ?? 'Inter');
  _setVal('cfg-font-size', p.base_font_size_pt ?? 10);
  _setVal('cfg-margin-top', p.margin_top_mm ?? 18);
  _setVal('cfg-margin-left', p.margin_left_mm ?? 18);
  _setVal('cfg-accent', p.accent_color ?? '#2563eb');
  _setVal('cfg-title-color', p.title_color ?? '#1e3a8a');
}

export function onTemplateNameChange() {
  if (!_template) return;
  const newName = _getVal('template-name-input');
  if (newName) _template.name = newName;
}

export function onOutputFilenameChange() {
  if (!_template) return;
  _template.output_filename = _getVal('cfg-output-filename') || 'cv';
}

export function onPageConfigChange() {
  if (!_template) return;
  _template.page.font_family = _getVal('cfg-font') || 'Inter';
  _template.page.base_font_size_pt = parseFloat(_getVal('cfg-font-size')) || 10;
  _template.page.margin_top_mm = parseFloat(_getVal('cfg-margin-top')) || 18;
  _template.page.margin_left_mm = parseFloat(_getVal('cfg-margin-left')) || 18;
  _template.page.accent_color = _getVal('cfg-accent') || '#2563eb';
  _template.page.title_color = _getVal('cfg-title-color') || '#1e3a8a';
  _notifyChange();
}

// ── Sections list ─────────────────────────────────────────────────────────────
function _renderSectionsList() {
  const ul = document.getElementById('sections-list');
  if (!ul || !_template) return;
  ul.innerHTML = '';

  const sorted = [..._template.sections].sort((a, b) => a.order - b.order);

  sorted.forEach((section, idx) => {
    const li = document.createElement('li');
    li.className = 'section-item';
    li.dataset.id = section.id;
    li.draggable = true;

    const titleText = section.config.section_title || _formatId(section.id);

    li.innerHTML = `
      <div class="section-item-header">
        <span class="drag-handle" title="Drag to reorder">⠿</span>
        <input type="checkbox" class="section-visible-check" ${section.visible ? 'checked' : ''}
               title="Toggle visibility" onchange="editor.toggleVisible('${section.id}', this.checked)" />
        <span class="section-name">${titleText}</span>
        <span class="section-type-badge">${section.type.replace('_block','').replace('_',' ')}</span>
        <button class="section-config-toggle" onclick="editor.toggleConfig('${section.id}')" title="Settings">⚙</button>
      </div>
      <div class="section-config-body" id="cfg-body-${section.id}">
        ${_buildConfigFields(section)}
      </div>
    `;

    _attachDragEvents(li);
    ul.appendChild(li);
  });
}

const _TEXT_ALIGN_TYPES = new Set(['header', 'text_block', 'skills_block', 'experience_block', 'education_block']);

const _TEXT_ALIGN_DEFAULTS = {
  header: 'center',
  text_block: 'justify',
  skills_block: 'left',
  experience_block: 'justify',
  education_block: 'left',
};

function _buildConfigFields(section) {
  const cfg = section.config;
  let html = '';
  if ('section_title' in cfg) {
    html += `<label>Section Title
      <input type="text" value="${cfg.section_title || ''}"
             oninput="editor.updateSectionConfig('${section.id}', 'section_title', this.value)" />
    </label>`;
  }
  if ('name_font_size_pt' in cfg) {
    html += `<label>Name Font Size (pt)
      <input type="number" value="${cfg.name_font_size_pt || 22}" min="14" max="36" step="1"
             oninput="editor.updateSectionConfig('${section.id}', 'name_font_size_pt', parseFloat(this.value))" />
    </label>`;
  }
  if (_TEXT_ALIGN_TYPES.has(section.type)) {
    const defaultAlign = _TEXT_ALIGN_DEFAULTS[section.type] || 'left';
    const current = cfg.text_align || defaultAlign;
    html += `<label>Text Align
      <select onchange="editor.updateSectionConfig('${section.id}', 'text_align', this.value)" class="cfg-select">
        ${['left','center','right','justify'].map(v =>
          `<option value="${v}"${current === v ? ' selected' : ''}>${v.charAt(0).toUpperCase() + v.slice(1)}</option>`
        ).join('')}
      </select>
    </label>`;
  }
  return html || '<p style="font-size:10px;color:#9ca3af">No configurable options</p>';
}

export function toggleVisible(sectionId, visible) {
  const sec = _template.sections.find(s => s.id === sectionId);
  if (sec) { sec.visible = visible; _notifyChange(); }
}

export function toggleConfig(sectionId) {
  const body = document.getElementById(`cfg-body-${sectionId}`);
  if (body) body.classList.toggle('open');
}

export function updateSectionConfig(sectionId, key, value) {
  const sec = _template.sections.find(s => s.id === sectionId);
  if (sec) { sec.config[key] = value; _notifyChange(); }
}

// ── Drag-and-drop reorder ─────────────────────────────────────────────────────
let _dragSrcId = null;

function _attachDragEvents(li) {
  li.addEventListener('dragstart', e => {
    _dragSrcId = li.dataset.id;
    li.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
  });
  li.addEventListener('dragend', () => li.classList.remove('dragging'));

  li.addEventListener('dragover', e => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    li.classList.add('drag-over');
  });
  li.addEventListener('dragleave', () => li.classList.remove('drag-over'));

  li.addEventListener('drop', e => {
    e.preventDefault();
    li.classList.remove('drag-over');
    if (_dragSrcId && _dragSrcId !== li.dataset.id) {
      _reorder(_dragSrcId, li.dataset.id);
    }
  });
}

function _reorder(srcId, targetId) {
  const sections = [..._template.sections].sort((a, b) => a.order - b.order);
  const srcIdx = sections.findIndex(s => s.id === srcId);
  const tgtIdx = sections.findIndex(s => s.id === targetId);
  if (srcIdx === -1 || tgtIdx === -1) return;
  const [moved] = sections.splice(srcIdx, 1);
  sections.splice(tgtIdx, 0, moved);
  sections.forEach((s, i) => { s.order = i; });
  _template.sections = sections;
  _renderSectionsList();
  _notifyChange();
}

// ── Save template ─────────────────────────────────────────────────────────────
export async function saveTemplate() {
  if (!_template) return;
  try {
    const res = await fetch(`/api/templates/${_template.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(_template),
    });
    if (!res.ok) throw new Error(await res.text());
    // Update the selector option text to reflect any name change
    const sel = document.getElementById('template-select');
    const opt = sel && sel.querySelector(`option[value="${_template.id}"]`);
    if (opt) opt.textContent = _template.name;
    alert('Template saved!');
  } catch (e) { alert('Save failed: ' + e.message); }
}

export async function deleteTemplate() {
  if (!_template) return;
  if (_template.id === 'default') { alert('The default template cannot be deleted.'); return; }
  if (!confirm(`Delete template "${_template.name}"? This cannot be undone.`)) return;
  try {
    const res = await fetch(`/api/templates/${_template.id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(await res.text());
    window.app && window.app.loadTemplates && window.app.loadTemplates();
  } catch (e) { alert('Delete failed: ' + e.message); }
}

export async function saveAsNew() {
  if (!_template) return;
  const name = prompt('Template name:', _template.name + ' (copy)');
  if (!name) return;
  const newTmpl = { ..._template, id: crypto.randomUUID(), name };
  try {
    const res = await fetch('/api/templates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newTmpl),
    });
    if (!res.ok) throw new Error(await res.text());
    _template = await res.json();
    alert(`Saved as "${name}"!`);
    // Refresh template selector
    window.app && window.app.loadTemplates && window.app.loadTemplates();
  } catch (e) { alert('Save failed: ' + e.message); }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function _notifyChange() {
  if (_onChangeCallback) _onChangeCallback(_template);
}

function _formatId(id) {
  return id.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function _setVal(id, val) {
  const el = document.getElementById(id);
  if (el) el.value = val;
}

function _getVal(id) {
  const el = document.getElementById(id);
  return el ? el.value : '';
}

// Expose to inline HTML handlers
window.editor = { toggleVisible, toggleConfig, updateSectionConfig, onPageConfigChange, onTemplateNameChange, onOutputFilenameChange, saveTemplate, saveAsNew, deleteTemplate };
