/* app.js — BOM UAT Dashboard v5 (Instant In-Memory Filtering + Continuous Live Proof Monitor + Editable Excel Table) */
'use strict';

// ── State ─────────────────────────────────────────────────────────────────────
const S = {
  rows: [], sorted: [], sortKey: null, sortAsc: true,
  running: false, pass: 0, fail: 0, skip: 0, total: 0, done: 0,
  startTime: null, timerHandle: null,
  tcDetail: {},
  showMonitor: true,
  currentPreset: 'All',
  proofGallery: [],
  allCases: null
};

// ── SSE connection ─────────────────────────────────────────────────────────────
let _es = null;
function connectSSE() {
  if (_es) _es.close();
  _es = new EventSource('/api/events');
  _es.onopen  = () => {
    setConn(true);
    updateMatchingCount();
  };
  _es.onerror = () => { setConn(false); setTimeout(connectSSE, 4000); };
  _es.onmessage = (e) => { try { onEvent(JSON.parse(e.data)); } catch {} };
}
function setConn(ok) {
  document.getElementById('conn-dot').className = 'conn-dot ' + (ok ? 'online' : 'offline');
  document.getElementById('conn-txt').textContent = ok ? 'Connected' : 'Disconnected';
}

// ── Event dispatcher ──────────────────────────────────────────────────────────
function onEvent({ type, data }) {
  switch (type) {
    case 'run_start':
      S.pass = S.fail = S.skip = S.done = 0;
      S.total = data.total; S.running = true; S.startTime = Date.now();
      setRunUI(true); showStatsBar(true);
      showProgress(true); updateProgress(0, data.total);
      startTimer();
      startLivePoll();
      updateMonitorBadge('RUNNING...', 'Testing in progress');
      log(`[RUN] Started — ${data.total} test cases`, 'info');
      break;


    case 'login_ok':
      log(`  Login OK [${data.role}] -> ${data.url}`, 'muted');
      updateMonitorMeta(data.tc_id, 'LOGGING IN', `Role: ${data.role}`);
      break;

    case 'tc_start':
      S.tcDetail[`${data.tc_id}||${data.role}||${data.type}`] = data;
      upsertRow({ 'TC ID': data.tc_id, Role: data.role,
        'Permission Type': data.type, Function: data.function,
        Status: 'Running', Comments: '', App: '', Elapsed: '', Screenshot: '',
        _step: data.step, _expected: data.expected });
      log(`  [START] [${data.tc_id}] ${data.type} | ${data.role}`, 'muted');
      updateMonitorMeta(data.tc_id, 'RUNNING', `${data.type} (${data.role})`);
      break;

    case 'tc_done': {
      const cls = data.status === 'Passed' ? 'ok' : (data.status === 'Failed' ? 'fail' : 'warn');
      log(`  [${data.status.toUpperCase()}] [${data.tc_id}] (${data.elapsed}s) — ${data.comment}`, cls);

      S.pass = data.pass; S.fail = data.fail; S.skip = data.skip;
      S.done = data.done; S.total = data.total;
      updateProgress(data.done, data.total);
      updateSidebarStats(data.done, data.pass, data.fail);
      updateStatsPills(data.done, data.pass, data.fail, data.skip);
      updateRetryBtn(data.fail);

      const key = `${data.tc_id}||${data.role}||${data.type}`;
      S.tcDetail[key] = { ...(S.tcDetail[key] || {}), ...data };

      upsertRow({ 'TC ID': data.tc_id, Role: data.role,
        'Permission Type': data.type, Function: data.function,
        Status: data.status, Comments: data.comment,
        App: data.app || '', Elapsed: data.elapsed ? `${data.elapsed}s` : '',
        Screenshot: data.screenshot || '' });

      updateMonitorMeta(data.tc_id, data.status, `Finished in ${data.elapsed}s`);

      // Advance queue badges sequentially to next pending cases
      updateMatchingCount();

      // Add to Proof Gallery (Latest on Top) & update monitor display
      if (data.screenshot) {

        document.getElementById('live-monitor-img').src = `/screenshots/${data.screenshot}`;
        const fullImg = document.getElementById('modal-live-full-img');
        if (fullImg) fullImg.src = `/screenshots/${data.screenshot}`;
        addProofGalleryItem(data.tc_id, data.status, data.role, data.screenshot, data.elapsed);
      }
      break;
    }

    case 'live_frame': {
      if (data.image) {
        document.getElementById('live-monitor-img').src = data.image;
        const fullImg = document.getElementById('modal-live-full-img');
        if (fullImg) fullImg.src = data.image;
      }
      if (data.label) {
        updateMonitorBadge(data.label, data.tc_id);
      }
      break;
    }

    case 'run_complete':
      log(`[COMPLETE] Run complete — ${data.done}/${data.total} | Pass: ${data.pass} Fail: ${data.fail}`, 'ok');
      S.running = false; setRunUI(false); stopTimer();
      updateRetryBtn(data.fail);
      updateMonitorBadge('COMPLETED', 'All tests done');
      buildSummary();
      break;

    case 'run_stopped':
      log(`[STOP] Stopped immediately by user`, 'warn');
      S.running = false; setRunUI(false); stopTimer();
      updateMonitorBadge('STOPPED', 'Run interrupted');
      break;

    case 'run_error':
      log(`[ERROR] ${data.error}`, 'fail');
      S.running = false; setRunUI(false); stopTimer();
      updateMonitorBadge('ERROR', 'Execution failed');
      break;

    case 'report_ready':
      log(`[REPORT] Report updated & saved`, 'ok');
      break;
  }
}

// ── Live Monitor & Latest-First Proof Gallery ──────────────────────────────────
function toggleLiveMonitor() {
  S.showMonitor = !S.showMonitor;
  const p = document.getElementById('live-monitor-panel');
  if (p) p.style.display = S.showMonitor ? 'flex' : 'none';
}

function openLiveFullscreen() {
  const curSrc = document.getElementById('live-monitor-img').src;
  const fullImg = document.getElementById('modal-live-full-img');
  if (fullImg) fullImg.src = curSrc;
  document.getElementById('modal-live-full').style.display = 'grid';
}

let _livePollTimer = null;
function startLivePoll() {
  if (_livePollTimer) clearInterval(_livePollTimer);
  _livePollTimer = setInterval(async () => {
    if (!S.running) return;
    try {
      const res = await fetch('/api/live_frame').then(r => r.json());
      if (res.image) {
        document.getElementById('live-monitor-img').src = res.image;
        const fullImg = document.getElementById('modal-live-full-img');
        if (fullImg) fullImg.src = res.image;
      }
      if (res.label) {
        updateMonitorBadge(res.label, res.tc_id);
      }
    } catch {}
  }, 300);
}
function stopLivePoll() {
  if (_livePollTimer) { clearInterval(_livePollTimer); _livePollTimer = null; }
}


function updateMonitorBadge(badgeText, infoText="") {
  const b = document.getElementById('monitor-badge');
  if (b) b.textContent = `${badgeText} ${infoText ? '· ' + infoText : ''}`;
  const mb = document.getElementById('modal-live-badge-txt');
  if (mb) mb.textContent = `${badgeText} ${infoText ? '· ' + infoText : ''}`;
}

function updateMonitorMeta(tcId, status, action) {
  document.getElementById('mon-tc-id').textContent = tcId || '-';
  document.getElementById('mon-status').textContent = status || '-';
  document.getElementById('mon-action').textContent = action || '-';
}

function addProofGalleryItem(tcId, status, role, screenshotName, elapsed) {
  const tip = document.getElementById('proof-empty-tip');
  if (tip) tip.style.display = 'none';

  const gallery = document.getElementById('proofs-gallery');
  if (!gallery) return;

  const item = document.createElement('div');
  item.className = 'proof-card';
  const stClass = status === 'Passed' ? 'b-pass' : status === 'Failed' ? 'b-fail' : 'b-skip';

  item.innerHTML = `
    <div class="proof-thumb-wrap" onclick="viewSS('${screenshotName}', '${tcId}')">
      <img src="/screenshots/${screenshotName}" alt="${tcId}" class="proof-thumb"/>
    </div>
    <div class="proof-info">
      <div class="proof-tc" onclick="viewSS('${screenshotName}', '${tcId}')">${tcId}</div>
      <div class="proof-role">${role}</div>
      <div class="proof-status"><span class="badge ${stClass}">${status}</span> <span class="proof-time">${elapsed}s</span></div>
    </div>
    <button class="btn-ghost btn-xs" onclick="viewSS('${screenshotName}', '${tcId}')">Preview</button>
  `;

  gallery.insertBefore(item, gallery.firstChild);
}

// ── Presets & Dynamic Counter & Live Queued Highlighting ───────────────────────
function selectPreset(preset) {
  S.currentPreset = preset;
  document.querySelectorAll('.btn-preset').forEach(b => {
    b.classList.toggle('active', b.dataset.preset === preset);
  });

  const typesContainer = document.getElementById('chip-types');
  const rolesContainer = document.getElementById('chip-roles');

  rolesContainer.querySelectorAll('.chip').forEach(c => c.classList.add('active'));

  if (preset === 'All') {
    typesContainer.querySelectorAll('.chip').forEach(c => c.classList.add('active'));
  } else {
    typesContainer.querySelectorAll('.chip').forEach(c => {
      const val = c.dataset.val;
      if (preset === 'Read' && val === 'Read') c.classList.add('active');
      else if (preset === 'Create' && val === 'Create') c.classList.add('active');
      else if (preset === 'Validate' && val.includes('Validate')) c.classList.add('active');
      else if (preset === 'Setting' && val.includes('Setting')) c.classList.add('active');
      else c.classList.remove('active');
    });
  }

  updateMatchingCount();
}

function toggleAdvancedFilters() {
  const container = document.getElementById('advanced-filters-container');
  const btn = document.getElementById('btn-toggle-adv');
  if (!container) return;
  const isHidden = container.style.display === 'none';
  container.style.display = isHidden ? 'block' : 'none';
  btn.textContent = isHidden ? 'Hide Advanced' : 'Advanced Filters';
}

async function loadAllTestCases(force = false) {
  if (S.allCases && S.allCases.length && !force) return S.allCases;
  try {
    const res = await fetch('/api/testcases').then(r => r.json());
    S.allCases = res.rows || [];
    return S.allCases;
  } catch (err) {
    console.error('[LOAD TESTCASES ERROR]', err);
    return [];
  }
}

async function updateMatchingCount() {
  const badge = document.getElementById('matched-count-badge');
  if (!badge) return;

  const allRows = await loadAllTestCases();

  const types = getChips('chip-types');
  const roles = getChips('chip-roles');
  const limit = parseInt(document.getElementById('inp-limit').value) || null;
  const tcRaw = document.getElementById('inp-tc-filter').value.trim();

  if (!types.length || !roles.length || !allRows.length) {
    badge.textContent = 'Matched: 0 cases';
    badge.className = 'matched-badge matched-zero';
    S.rows = []; renderTable(); renderStatusChart(0, 0);
    return;
  }

  // Instant pure JavaScript filter (<1ms)
  let matched = allRows.filter(r =>
    types.includes(r['Permission Type']) && roles.includes(r['Role'])
  );

  if (tcRaw) {
    const ids = tcRaw.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
    if (ids.length) {
      matched = matched.filter(r => ids.some(id => String(r['TC ID']||'').toLowerCase().includes(id)));
    }
  }

  const totalMatched = matched.length;
  badge.textContent = `Matched: ${totalMatched} cases (${roles.length} Role${roles.length > 1 ? 's' : ''})`;
  badge.className = 'matched-badge';


  const oldRows = [...(S.rows || [])];
  let queueCounter = 0;

  S.rows = matched.map((r) => {
    const existing = oldRows.find(ex => ex && ex['TC ID'] === r['TC ID'] && ex['Role'] === r['Role'] && ex['Permission Type'] === r['Permission Type']);
    const status = existing?.Status || r.Status || '';
    const isPending = !status || status === 'Pending';

    let qIdx = null;
    if (isPending && limit && queueCounter < limit) {
      queueCounter++;
      qIdx = queueCounter;
    }

    return {
      'TC ID': r['TC ID'] || '',
      'Role': r['Role'] || '',
      'Permission Type': r['Permission Type'] || '',
      'Function': r['Function'] || '',
      'Module': r['Module'] || '',
      Status: status,
      Comments: existing?.Comments || r.Comments || '',
      App: existing?.App || r.App || '',
      Elapsed: existing?.Elapsed || r.Elapsed || '',
      Screenshot: existing?.Screenshot || r.Screenshot || '',
      _queuedIndex: qIdx,
      _step: r['ขั้นตอนทดสอบ'] || '',
      _expected: r['ผลที่คาดหวัง'] || ''
    };
  });

  renderTable();
  renderStatusChart(totalMatched, queueCounter);
}


// ── Live Breakdown Graph Widget ────────────────────────────────────────────────
function renderStatusChart(totalMatched, queuedCount) {
  const pass = S.rows.filter(r => r.Status === 'Passed').length;
  const fail = S.rows.filter(r => r.Status === 'Failed').length;
  const total = totalMatched || 1;

  const pctPass = Math.round((pass / total) * 100);
  const pctFail = Math.round((fail / total) * 100);
  const pctQueued = Math.round((queuedCount / total) * 100);
  const pctMatched = Math.max(0, 100 - pctPass - pctFail - pctQueued);

  document.getElementById('cbar-pass').style.width = pctPass + '%';
  document.getElementById('cbar-fail').style.width = pctFail + '%';
  document.getElementById('cbar-queued').style.width = pctQueued + '%';
  document.getElementById('cbar-matched').style.width = pctMatched + '%';

  document.getElementById('lg-val-pass').textContent = pass;
  document.getElementById('lg-val-fail').textContent = fail;
  document.getElementById('lg-val-queued').textContent = queuedCount;
  document.getElementById('lg-val-matched').textContent = totalMatched;

  document.getElementById('chart-stats-summary').textContent = `${totalMatched} Matched | ${queuedCount} Queued Target`;
}

// ── Logging ────────────────────────────────────────────────────────────────────
function now() {
  return new Date().toLocaleTimeString('en-GB', { hour12: false });
}
function log(msg, cls = '') {
  const append = (boxId) => {
    const box  = document.getElementById(boxId);
    if (!box) return;
    const line = document.createElement('div');
    const ts   = document.createElement('span');
    ts.className = 'log-ts'; ts.textContent = now();
    const txt = document.createTextNode(msg);
    line.className = cls ? `log-${cls}` : '';
    line.appendChild(ts); line.appendChild(txt);
    box.appendChild(line);
    if (boxId === 'live-log' && document.getElementById('chk-autoscroll')?.checked)
      box.scrollTop = box.scrollHeight;
    if (boxId === 'full-log') box.scrollTop = box.scrollHeight;
    while (box.children.length > 500) box.removeChild(box.firstChild);
  };
  append('live-log');
  append('full-log');
}
function clearLog() {
  ['live-log', 'full-log'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = '';
  });
}

// ── Live Interactive Excel Table Management ────────────────────────────────────
function upsertRow(row) {
  const key = `${row['TC ID']}||${row['Role']}||${row['Permission Type']}`;
  const idx = S.rows.findIndex(r =>
    `${r['TC ID']}||${r['Role']}||${r['Permission Type']}` === key);
  if (idx >= 0) S.rows[idx] = { ...S.rows[idx], ...row };
  else S.rows.push(row);
  renderTable();
}

function renderTable() {
  const q     = (document.getElementById('tbl-search')?.value || '').toLowerCase();
  const fSt   = document.getElementById('filter-status')?.value || '';
  const fRole = document.getElementById('filter-role')?.value || '';
  const fType = document.getElementById('filter-type')?.value || '';

  S.sorted = S.rows.filter(r => {
    if (fSt   && r.Status !== fSt) return false;
    if (fRole && r.Role   !== fRole) return false;
    if (fType && r['Permission Type'] !== fType) return false;
    if (q && !Object.values(r).some(v => String(v||'').toLowerCase().includes(q))) return false;
    return true;
  });

  if (S.sortKey) {
    S.sorted.sort((a, b) => {
      const va = String(a[S.sortKey]||''), vb = String(b[S.sortKey]||'');
      return S.sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
    });
  }

  const tbody = document.getElementById('tbl-body');
  tbody.innerHTML = '';

  S.sorted.forEach(row => {
    const key = `${row['TC ID']}||${row['Role']}||${row['Permission Type']}`;
    const st = row.Status || '';
    const isQueued = row._queuedIndex != null;
    const rc = isQueued ? 'row-queued' : (st === 'Passed' ? 'row-pass' : st === 'Failed' ? 'row-fail' : st === 'Running' ? 'row-run' : 'row-skip');
    const ss = row.Screenshot
      ? `<button class="btn-primary btn-xs" title="Preview screenshot" onclick="viewSS('${row.Screenshot}', '${row['TC ID']}')">Preview</button>` : '';

    const queueBadge = isQueued
      ? `<span class="badge b-queued" title="Queued target execution #${row._queuedIndex}">#${row._queuedIndex}</span>`
      : `<span class="badge b-wait">-</span>`;

    const statusSelect = `
      <select class="inp inp-xs sel-status-editable ${st === 'Passed' ? 'st-pass' : st === 'Failed' ? 'st-fail' : ''}" onchange="handleCellEdit('${key}', 'Status', this.value)" title="Click to edit status">
        <option value="" ${!st ? 'selected' : ''}>Pending</option>
        <option value="Passed" ${st==='Passed' ? 'selected' : ''}>Passed</option>
        <option value="Failed" ${st==='Failed' ? 'selected' : ''}>Failed</option>
        <option value="Skipped" ${st==='Skipped' ? 'selected' : ''}>Skipped</option>
        <option value="Running" ${st==='Running' ? 'selected' : ''}>Running</option>
      </select>`;

    const tr = document.createElement('tr');
    tr.className = rc;
    tr.innerHTML = `
      <td>${queueBadge}</td>
      <td><span class="cell-tc" onclick="openDetail('${key}')" title="Click for details">${row['TC ID']||''}</span></td>
      <td><span class="badge b-role">${row.Role||''}</span></td>
      <td><span class="badge b-type">${row['Permission Type']||''}</span></td>
      <td style="font-size:11px;color:var(--muted2)">${row.App||''}</td>
      <td class="cell-editable" contenteditable="true" onblur="handleCellEdit('${key}', 'Function', this.innerText)" title="Click to edit Function">${row.Function||''}</td>
      <td>${statusSelect}</td>
      <td class="cell-editable cell-cmt" contenteditable="true" onblur="handleCellEdit('${key}', 'Comments', this.innerText)" title="Click to edit Comment">${row.Comments||''}</td>
      <td class="cell-time">${row.Elapsed||''}</td>
      <td>${ss}</td>`;
    tbody.appendChild(tr);
  });


  document.getElementById('tbl-count').textContent = S.sorted.length;
}

// In-place Excel cell editing handler
async function handleCellEdit(key, field, newValue) {
  const val = String(newValue||'').trim();
  const row = S.rows.find(r => `${r['TC ID']}||${r['Role']}||${r['Permission Type']}` === key);
  if (row) {
    row[field] = val;
    if (S.allCases) {
      const c = S.allCases.find(r => `${r['TC ID']}||${r['Role']}||${r['Permission Type']}` === key);
      if (c) c[field] = val;
    }
    if (field === 'Status') {
      updateMatchingCount();
    } else {
      renderTable();
    }
    log(`[EDIT] ${row['TC ID']} ${field} updated -> "${val.slice(0,30)}"`, 'info');
    try {
      await fetch('/api/update_row', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tc_id: row['TC ID'], role: row['Role'], field, value: val })
      });
    } catch {}
  }
}


function sortTable(key) {
  S.sortAsc = S.sortKey === key ? !S.sortAsc : true;
  S.sortKey = key;
  renderTable();
}
function clearResults() {
  S.rows = []; renderTable(); clearLog();
  showStatsBar(false);
  document.getElementById('tbl-count').textContent = '';
  renderStatusChart(0, 0);
}

// ── Progress & stats ───────────────────────────────────────────────────────────
function showProgress(show) {
  document.getElementById('prog-card').style.display  = show ? 'block' : 'none';
  document.getElementById('ctrl-btns').style.display  = show ? 'flex'  : 'none';
}
function updateProgress(done, total) {
  const pct = total ? Math.round(done / total * 100) : 0;
  const bar = document.getElementById('prog-bar');
  bar.style.width = pct + '%';
  bar.className = S.running ? 'prog-bar prog-bar-active' : 'prog-bar';
  document.getElementById('prog-pct').textContent  = pct + '%';
  document.getElementById('prog-frac').textContent = `${done} / ${total}`;
}
function updateSidebarStats(done, pass, fail) {
  document.getElementById('sb-total').textContent = done;
  document.getElementById('sb-pass').textContent  = pass;
  document.getElementById('sb-fail').textContent  = fail;
}
function showStatsBar(show) {
  document.getElementById('stats-bar').style.display = show ? 'flex' : 'none';
}
function updateStatsPills(done, pass, fail, skip) {
  const rate = done ? Math.round(pass / done * 100) : 0;
  document.getElementById('pill-total').textContent = `${done} Total`;
  document.getElementById('pill-pass').textContent  = `${pass} Passed`;
  document.getElementById('pill-fail').textContent  = `${fail} Failed`;
  document.getElementById('pill-skip').textContent  = `${skip} Skipped`;
  document.getElementById('pill-rate').textContent  = `${rate}% Pass Rate`;
}
function updateRetryBtn(fail) {
  document.getElementById('btn-retry').style.display = fail > 0 ? 'inline-block' : 'none';
}

// ── Timer ──────────────────────────────────────────────────────────────────────
function startTimer() {
  S.startTime = Date.now();
  S.timerHandle = setInterval(() => {
    const sec  = Math.floor((Date.now() - S.startTime) / 1000);
    const m    = Math.floor(sec / 60).toString().padStart(2,'0');
    const s    = (sec % 60).toString().padStart(2,'0');
    document.getElementById('pill-time').textContent = `Time: ${m}:${s}`;
  }, 1000);
}
function stopTimer() {
  clearInterval(S.timerHandle);
}

// ── Run control ────────────────────────────────────────────────────────────────
function getChips(id) {
  return [...document.querySelectorAll(`#${id} .chip.active`)].map(c => c.dataset.val);
}

async function startRun() {
  if (S.running) return;
  const types = getChips('chip-types');
  const roles = getChips('chip-roles');
  if (!types.length || !roles.length) {
    alert('Select at least one type and one role.'); return;
  }
  const limit       = parseInt(document.getElementById('inp-limit').value) || null;
  const headless    = document.getElementById('inp-mode').value === '1';
  const proof_delay = parseFloat(document.getElementById('inp-proof-delay').value) || 1.5;
  const tcRaw       = document.getElementById('inp-tc-filter').value.trim();
  let tc_ids        = tcRaw ? tcRaw.split(',').map(s => s.trim()).filter(Boolean) : null;

  // Auto-pick next queued target test cases matching the #1, #2... badges in the table
  if (!tc_ids && limit && S.rows.length) {
    const queued = S.rows.filter(r => r._queuedIndex != null);
    if (queued.length) {
      tc_ids = queued.map(r => r['TC ID']);
      log(`[QUEUE] Selected next ${tc_ids.length} pending case(s): ${tc_ids.join(', ')}`, 'info');
    }
  }


  clearLog();
  const r = await fetch('/api/run', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ types, roles, limit, headless, tc_ids, proof_delay })
  }).then(r => r.json());


  if (r.error) { alert(r.error); }
}

async function retryFailed() {
  if (S.running) return;
  const headless    = document.getElementById('inp-mode').value === '1';
  const proof_delay = parseFloat(document.getElementById('inp-proof-delay').value) || 1.5;
  const r = await fetch('/api/run', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ retry_failed: true, headless, proof_delay })
  }).then(r => r.json());
  if (r.error) alert(r.error);
}

function stopRun() {
  log('[STOP] Requesting instant stop...', 'warn');
  updateMonitorBadge('STOPPING...', 'Closing browser session');
  fetch('/api/stop', { method: 'POST' });
}

function setRunUI(running) {
  S.running = running;
  document.getElementById('btn-run').style.display  = running ? 'none' : 'inline-block';
  document.getElementById('btn-stop').style.display = running ? 'inline-block' : 'none';
  if (!running) {
    const bar = document.getElementById('prog-bar');
    if (bar) bar.className = 'prog-bar';
  }
}

// ── Save & Sync vs Download Excel Options ──────────────────────────────────────
async function syncCurrentEdits() {
  const syncBtn = document.getElementById('btn-sync-report');
  const oldTxt  = syncBtn ? syncBtn.textContent : 'Save & Sync';
  if (syncBtn) syncBtn.textContent = 'Syncing Excel...';

  try {
    const res = await fetch('/api/save_report', { method: 'POST' }).then(r => r.json());
    log(`[SYNC] Saved and synced edits to current report file (${res.count||0} records)`, 'ok');
    if (syncBtn) {
      syncBtn.textContent = 'Synced to test_results.xlsx';
      setTimeout(() => { syncBtn.textContent = oldTxt; }, 2200);
    }
  } catch (err) {
    log(`[SYNC ERROR] Failed to sync edits: ${err}`, 'fail');
    if (syncBtn) syncBtn.textContent = oldTxt;
  }
}

function downloadReport() {
  log('[DOWNLOAD] Downloading test_results.xlsx...', 'info');
  window.open('/api/report', '_blank');
}

async function saveAndDownloadReport() {
  await syncCurrentEdits();
  downloadReport();
}


// ── Preview ────────────────────────────────────────────────────────────────────
async function previewTests() {
  updateMatchingCount();
  log(`[PREVIEW] Displayed matched execution queue`, 'info');
}

// ── TC Detail modal ────────────────────────────────────────────────────────────
function openDetail(key) {
  const data = S.tcDetail[key];
  const row  = S.rows.find(r =>
    `${r['TC ID']}||${r['Role']}||${r['Permission Type']}` === key);
  if (!row && !data) return;

  const d = { ...(data||{}), ...(row||{}) };
  const bd = `<span class="badge b-wait">${d.Status||'Pending'}</span>`;

  document.getElementById('modal-tc-body').innerHTML = `
    <div class="modal-title">${d['TC ID'] || ''} — ${d.Function || ''}</div>
    <div class="modal-row"><span class="modal-key">Status</span><span class="modal-val">${bd}</span></div>
    <div class="modal-row"><span class="modal-key">Role</span><span class="modal-val">${d.Role||''}</span></div>
    <div class="modal-row"><span class="modal-key">Type</span><span class="modal-val">${d['Permission Type']||''}</span></div>
    <div class="modal-row"><span class="modal-key">App</span><span class="modal-val">${d.App||d.app||''}</span></div>
    <div class="modal-row"><span class="modal-key">Elapsed</span><span class="modal-val">${d.Elapsed||d.elapsed||'-'}</span></div>
    <div class="modal-row"><span class="modal-key">Comment</span><span class="modal-val">${d.Comments||d.comment||'-'}</span></div>
    ${d._expected ? `<div class="modal-row"><span class="modal-key">Expected</span><span class="modal-val">${d._expected}</span></div>` : ''}
    ${d._step     ? `<div class="flt-label" style="margin-top:12px">Test Steps</div><div class="modal-step">${d._step}</div>` : ''}
    ${d.Screenshot||d.screenshot ? `<div style="margin-top:12px"><button class="btn-primary btn-sm" onclick="viewSS('${d.Screenshot||d.screenshot}', '${d['TC ID']}')">Preview Full Proof</button></div>` : ''}
  `;
  document.getElementById('modal-tc').style.display = 'grid';
}

// ── Screenshot modal ───────────────────────────────────────────────────────────
function viewSS(name, title="") {
  const titleEl = document.getElementById('modal-ss-title');
  if (titleEl) titleEl.textContent = title ? `Proof Evidence — ${title}` : 'Proof Screenshot';
  document.getElementById('modal-ss-img').src = `/screenshots/${name}`;
  document.getElementById('modal-ss').style.display = 'grid';
}
function closeModal(id) { document.getElementById(id).style.display = 'none'; }

// Keyboard shortcuts
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    closeModal('modal-tc');
    closeModal('modal-ss');
    closeModal('modal-live-full');
  }
});

// ── Report / Export ────────────────────────────────────────────────────────────
function exportCSV() {
  const rows  = S.sorted.length ? S.sorted : S.rows;
  if (!rows.length) { alert('No data to export'); return; }
  const cols  = ['TC ID','Role','Permission Type','App','Function','Status','Comments','Elapsed'];
  const lines = [cols.join(','),
    ...rows.map(r => cols.map(c => `"${String(r[c]||'').replace(/"/g,'""')}"`).join(','))
  ];
  const a = document.createElement('a');
  a.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent('\ufeff' + lines.join('\r\n'));
  a.download = `bom_uat_${new Date().toISOString().slice(0,10)}.csv`;
  a.click();
}

// ── Summary panel ──────────────────────────────────────────────────────────────
async function buildSummary() {
  const data = await fetch('/api/results').then(r => r.json());
  const rows = data.results || [];
  if (!rows.length) { document.getElementById('summary-body').innerHTML = '<p style="color:var(--muted2);padding:16px">No results yet</p>'; return; }

  const total = rows.length;
  const pass  = rows.filter(r => r.Status === 'Passed').length;
  const fail  = rows.filter(r => r.Status === 'Failed').length;
  const skip  = rows.filter(r => r.Status === 'Skipped').length;
  const rate  = total ? Math.round(pass / total * 100) : 0;

  const byRole = groupBy(rows, 'Role');
  const byType = groupBy(rows, 'Permission Type');

  document.getElementById('summary-body').innerHTML = `
    <div class="sum-grid">
      <div class="sum-card s-total"><div class="sum-lbl">Total</div><div class="sum-val">${total}</div></div>
      <div class="sum-card s-pass"><div class="sum-lbl">Passed</div><div class="sum-val">${pass}</div></div>
      <div class="sum-card s-fail"><div class="sum-lbl">Failed</div><div class="sum-val">${fail}</div></div>
      <div class="sum-card s-skip"><div class="sum-lbl">Skipped</div><div class="sum-val">${skip}</div></div>
      <div class="sum-card s-rate"><div class="sum-lbl">Pass Rate</div><div class="sum-val">${rate}%</div></div>
    </div>
    <div class="breakdown-grid">
      ${buildBreakdown('By Role', byRole, total)}
      ${buildBreakdown('By Permission Type', byType, total)}
    </div>
  `;
}

function groupBy(arr, key) {
  return arr.reduce((acc, r) => {
    const k = r[key] || '(unknown)';
    if (!acc[k]) acc[k] = [];
    acc[k].push(r);
    return acc;
  }, {});
}

function buildBreakdown(title, groups, grandTotal) {
  const rows = Object.entries(groups).map(([name, items]) => {
    const p = items.filter(r => r.Status === 'Passed').length;
    const f = items.filter(r => r.Status === 'Failed').length;
    const pct = items.length ? Math.round(p / items.length * 100) : 0;
    return `<div class="brk-row">
      <div class="brk-name">${name}</div>
      <div class="brk-total">${items.length}</div>
      <div class="brk-bar-bg"><div class="brk-bar" style="width:${pct}%"></div></div>
      <div class="brk-pct" style="color:${pct>=70?'var(--green)':pct>=40?'var(--yellow)':'var(--red)'}">${pct}%</div>
    </div>`;
  }).join('');
  return `<div class="brk-card"><h3>${title}</h3>${rows}</div>`;
}

// ── Config panel ───────────────────────────────────────────────────────────────
const CFG_KEY = 'bom_uat_cfg_v2';
const DEF_CFG = {
  credentials: {
    'Super Admin':   { username:'uat.super_admin',  password:'Uat@super_admin#2026'  },
    'Admin':         { username:'uat.admin',         password:'Uat@admin#2026'         },
    'Supervisor':    { username:'uat.supervisor',    password:'Uat@supervisor#2026'    },
    'Super User':    { username:'uat.super_user',    password:'Uat@super_user#2026'    },
    'User(Cashier)': { username:'uat.user',          password:'Uat@user#2026'          },
    'Outsource':     { username:'uat.outsource',     password:'Uat@outsource#2026'     },
  },
  idm:  { username:'cmp.aa', password:'THPCore@2024' },
  site: { url:'https://reg1-bom-uat.thpc.cc', db:'13000' },
  aliases: {
    'Point of Sale': ['Point of Sale','Sessions'],
    'Sales':         ['Sales'], 'Accounting':['Accounting'],
    'Purchase':      ['Purchase'], 'Inventory':['Inventory'],
    'Request':       ['Request','Expenses','My Expenses'],
    'Fleet':         ['Fleet'], 'MPOS':['MPOS'],
  }
};
function loadCfg() { try { return JSON.parse(localStorage.getItem(CFG_KEY)) || DEF_CFG; } catch { return DEF_CFG; } }

function buildConfigPanel() {
  const cfg  = loadCfg();
  const grid = document.getElementById('config-grid');
  grid.innerHTML = '';

  const site = card('Site & Database', `
    <div class="cfg-row"><label>Site URL</label><input id="c-site-url" value="${cfg.site.url}"/></div>
    <div class="cfg-row"><label>Database</label><input id="c-site-db" value="${cfg.site.db}"/></div>
  `);
  grid.appendChild(site);

  const idm = card('IDM Credentials', `
    <div class="cfg-row"><label>Username</label><input id="c-idm-u" value="${cfg.idm.username}"/></div>
    <div class="cfg-row"><label>Password</label><input id="c-idm-p" type="password" value="${cfg.idm.password}"/></div>
  `);
  grid.appendChild(idm);

  Object.entries(cfg.credentials).forEach(([role, cred]) => {
    const rid = role.replace(/[^a-z0-9]/gi,'_');
    grid.appendChild(card(role, `
      <div class="cfg-row"><label>Username</label><input id="c-${rid}-u" value="${cred.username}"/></div>
      <div class="cfg-row"><label>Password</label><input id="c-${rid}-p" type="password" value="${cred.password}"/></div>
    `));
  });

  document.getElementById('cfg-aliases').value = JSON.stringify(cfg.aliases, null, 2);
}

function card(title, html) {
  const d = document.createElement('div');
  d.className = 'cfg-card';
  d.innerHTML = `<h3>${title}</h3>${html}`;
  return d;
}

function saveConfig() {
  const cfg = loadCfg();
  cfg.site.url = document.getElementById('c-site-url').value;
  cfg.site.db  = document.getElementById('c-site-db').value;
  cfg.idm.username = document.getElementById('c-idm-u').value;
  cfg.idm.password = document.getElementById('c-idm-p').value;
  Object.keys(cfg.credentials).forEach(role => {
    const rid = role.replace(/[^a-z0-9]/gi,'_');
    const u = document.getElementById(`c-${rid}-u`);
    const p = document.getElementById(`c-${rid}-p`);
    if (u) cfg.credentials[role].username = u.value;
    if (p) cfg.credentials[role].password = p.value;
  });
  try { cfg.aliases = JSON.parse(document.getElementById('cfg-aliases').value); } catch {}
  localStorage.setItem(CFG_KEY, JSON.stringify(cfg));

  const btn = document.querySelector('[onclick="saveConfig()"]');
  const orig = btn.textContent;
  btn.textContent = 'Saved!';
  setTimeout(() => { btn.textContent = orig; }, 1500);
}

// ── Panel navigation ───────────────────────────────────────────────────────────
function showPanel(id, btn) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('panel-' + id).classList.add('active');
  if (btn) btn.classList.add('active');
  if (id === 'config')  buildConfigPanel();
  if (id === 'results') buildSummary();
}

// ── Boot ───────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.chip').forEach(c =>
    c.addEventListener('click', () => {
      c.classList.toggle('active');
      updateMatchingCount();
    }));

  connectSSE();
  log('Dashboard ready — choose a test preset or configure filters.', 'muted');
  updateMatchingCount();

  fetch('/api/state').then(r => r.json()).then(d => {
    if (d.results?.length) {
      S.rows = d.results.map(r => ({
        ...r, App: r.App||'', Elapsed: r.Elapsed||r.elapsed||'',
        Screenshot: r.Screenshot||r.screenshot||''
      }));
      S.pass = d.pass||0; S.fail = d.fail||0; S.skip = d.skip||0;
      S.done = d.done||0; S.total = d.total||0;
      renderTable();
      showStatsBar(true);
      updateStatsPills(d.done, d.pass||0, d.fail||0, d.skip||0);
      updateSidebarStats(d.done, d.pass||0, d.fail||0);
      if (d.fail > 0) updateRetryBtn(d.fail);
      log(`Restored ${d.results.length} results from last run.`, 'info');
    }
  }).catch(() => {});
});
