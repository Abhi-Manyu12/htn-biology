(() => {
  'use strict';
  const catalog = window.EXPERIMENT_CATALOG;
  const labels = window.EXPERIMENT_LABELS;
  const replay = window.ExperimentReplay;
  const $ = id => document.getElementById(id);
  const canvas = $('replay-canvas');
  const ctx = canvas.getContext('2d');
  const FORMAT = {fps: 30, bitsPerSecond: 6000000, finishHoldMs: 600,
    mimeTypes: ['video/webm;codecs=vp9', 'video/webm;codecs=vp8', 'video/webm', 'video/mp4'],
    width: 1440, height: 720, mobileWidth: 600, mobileHeight: 1280};
  const colors = Object.fromEntries(['bg', 'bg-panel', 'border', 'text', 'text-dim', 'accent', 'radius', 'capture', 'auxiliary', 'danger', 'scaffold']
    .map(name => [name, getComputedStyle(document.documentElement).getPropertyValue(`--${name}`).trim()]));
  const number = (value, digits = 2) => value == null ? '—' : Number(value).toLocaleString(undefined, {maximumFractionDigits: digits, minimumFractionDigits: digits});
  const controllerName = id => labels.controllers[id] || id;
  const scenarioName = id => labels.scenarios[id] || id;
  let studyId = 'e1';
  let study = null;
  let selectedCase = null;
  let time = 0;
  let playing = false;
  let lastFrame = null;
  let animationId = null;
  let generation = 0;
  let recorder = null;
  let stream = null;
  let finishTimer = null;
  let recordingFailed = false;
  let recordingInterrupted = false;
  let videoUrl = null;
  const loaders = new Map();

  function element(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  }

  function message(text = '') { $('message').textContent = text; }
  function selectedRuns() {
    if (!selectedCase) return [];
    const ids = [$('left-select').value];
    if ($('compare-toggle').checked) ids.push($('right-select').value);
    return ids.map(id => selectedCase.runs.find(run => run.id === id)).filter(Boolean);
  }

  function setPlaying(value) {
    playing = value;
    lastFrame = null;
    $('play').textContent = value ? labels.text.pause : labels.text.play;
    $('play').setAttribute('aria-label', value ? labels.ui.pauseAria : labels.ui.playAria);
    if (animationId !== null) cancelAnimationFrame(animationId);
    animationId = value ? requestAnimationFrame(tick) : null;
  }

  function tick(stamp) {
    if (!playing) return;
    if (lastFrame !== null) time += (stamp - lastFrame) / 1000 * Number($('speed').value);
    lastFrame = stamp;
    const end = replay.duration(selectedRuns());
    time = Math.min(time, end);
    render();
    if (time >= end) {
      setPlaying(false);
      if (recorder && recorder.state === 'recording') finishTimer = setTimeout(stopRecording, FORMAT.finishHoldMs);
    } else animationId = requestAnimationFrame(tick);
  }

  function invalidateVideo() {
    if (videoUrl) URL.revokeObjectURL(videoUrl);
    videoUrl = null;
    const previous = $('video-download');
    if (previous) previous.remove();
  }

  function controls(enabled) {
    document.querySelectorAll('.study-tabs button, #scenario-select, #case-select, #left-select, #right-select, #compare-toggle, #play, #restart, #timeline, #speed, #event-markers button')
      .forEach(node => { node.disabled = !enabled; });
    $('export').disabled = !enabled || !canRecord();
  }

  function loadBundle(id) {
    if (window.EXPERIMENT_STUDIES[id]) return Promise.resolve(window.EXPERIMENT_STUDIES[id]);
    if (loaders.has(id)) return loaders.get(id);
    const pending = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      // id comes exclusively from the local catalog, never from a URL or source path.
      script.src = `experiments/${id}.js`;
      script.onload = () => {
        const value = window.EXPERIMENT_STUDIES[id];
        if (!value || value.id !== id || !value.cases.length) { script.remove(); loaders.delete(id); reject(new Error(labels.text.loadError)); }
        else resolve(value);
      };
      script.onerror = () => { script.remove(); loaders.delete(id); reject(new Error(labels.text.loadError)); };
      document.head.append(script);
    });
    loaders.set(id, pending);
    return pending;
  }

  function chip(text) { return element('span', text, 'summary-chip'); }

  async function selectStudy(id) {
    if (!Object.hasOwn(catalog, id) || recorder) return;
    const token = ++generation;
    studyId = id;
    study = null;
    selectedCase = null;
    setPlaying(false);
    invalidateVideo();
    controls(false);
    document.querySelectorAll('[role="tab"]').forEach(tab => {
      const active = tab.dataset.study === id;
      tab.setAttribute('aria-selected', String(active));
      tab.tabIndex = active ? 0 : -1;
      // Tabs stay usable while a bundle loads; stale results are discarded below.
      tab.disabled = false;
    });
    const info = catalog[id];
    $('study-panel').setAttribute('aria-labelledby', `tab-${id}`);
    $('study-title').textContent = info.title;
    $('study-description').textContent = info.description;
    $('evidence-link').href = info.evidence;
    $('study-summary').replaceChildren();
    $('construction-panel').hidden = id !== 'construction';
    $('replay-panel').hidden = id === 'construction';
    if (id === 'construction') {
      $('study-panel').setAttribute('aria-busy', 'false');
      $('construction-frame').src = $('construction-select').value;
      message();
      return;
    }
    $('construction-frame').removeAttribute('src');
    $('study-panel').setAttribute('aria-busy', 'true');
    $('outcomes').replaceChildren();
    $('aggregate-body').replaceChildren();
    $('event-markers').replaceChildren();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    message(labels.text.loading);
    try {
      const loaded = await loadBundle(id);
      if (token !== generation) return;
      study = loaded;
      $('study-summary').replaceChildren(chip(`${number(study.total_trials, 0)} ${labels.ui.studyTrials}`),
        chip(`${study.cases.length} ${labels.ui.demoCases}`), chip(`${labels.ui.representativeSeed} ${study.cases[0].seed}`), chip(labels.text.summaryNote));
      const scenarios = [...new Set(study.cases.map(item => item.scenario))];
      $('scenario-select').replaceChildren(...scenarios.map(value => new Option(scenarioName(value), value)));
      if (scenarios.includes('damage_single')) $('scenario-select').value = 'damage_single';
      if (scenarios.includes('permanent_anchor')) $('scenario-select').value = 'permanent_anchor';
      $('study-caveat').textContent = info.caveat;
      $('aggregate-silk-label').textContent = `${id === 'moving' ? labels.ui.silkChord : labels.ui.actorSilk} (${labels.ui.cm})`;
      $('render-note').textContent = id === 'moving' ? labels.text.movingGeometry : labels.text.schematic;
      message(canRecord() ? '' : labels.text.unsupported);
      fillCases();
    } catch {
      if (token === generation) message(labels.text.loadError);
    } finally {
      if (token === generation) $('study-panel').setAttribute('aria-busy', 'false');
    }
  }

  function conditions(item) {
    const config = item.config;
    if (studyId === 'moving') return `${labels.policies[item.policy]} · ${config.radial_count} ${labels.ui.radii} · ${config.amplitude_cm} ${labels.ui.cm} · ${labels.ui.seed} ${item.seed}`;
    return [item.suite, `${config.sectors} ${labels.ui.sectors}`, `${config.amplitude_cm} ${labels.ui.cm} / ${config.frequency_hz} ${labels.ui.hz}`,
      `${config.silk_cm} ${labels.ui.cm} ${labels.ui.stock}`, `${labels.ui.depth} ${config.depth}`, `${labels.ui.seed} ${item.seed}`].filter(Boolean).join(' · ');
  }

  function fillCases() {
    if (!study) return;
    const cases = study.cases.filter(item => item.scenario === $('scenario-select').value);
    $('case-select').replaceChildren(...cases.map(item => new Option(conditions(item), item.id)));
    selectCase();
  }

  function selectCase() {
    selectedCase = study?.cases.find(item => item.id === $('case-select').value) || null;
    setPlaying(false);
    invalidateVideo();
    time = 0;
    if (!selectedCase) { controls(false); message(labels.text.noCases); return; }
    for (const id of ['left-select', 'right-select']) {
      $(id).replaceChildren(...selectedCase.runs.map(run => new Option(controllerName(run.id), run.id)));
    }
    const preferred = catalog[studyId].preferred;
    $('left-select').value = selectedCase.runs.some(run => run.id === preferred[0]) ? preferred[0] : selectedCase.runs[0].id;
    $('right-select').value = selectedCase.runs.some(run => run.id === preferred[1]) ? preferred[1] : selectedCase.runs.at(-1).id;
    updatePair();
  }

  function updatePair() {
    if (!selectedCase) return;
    setPlaying(false);
    invalidateVideo();
    const runs = selectedRuns();
    message(canRecord() ? '' : labels.text.unsupported);
    time = 0;
    $('timeline').max = Math.max(replay.duration(runs), .01);
    $('right-field').hidden = !$('compare-toggle').checked;
    $('case-caption').textContent = `${scenarioName(selectedCase.scenario)} · ${conditions(selectedCase)}`;
    controls(true);
    $('right-select').disabled = !$('compare-toggle').checked;
    $('outcomes').classList.toggle('single', runs.length === 1);
    $('pair-verdict').textContent = runs.length === 1 ? labels.text.singleRun
      : replay.physicalMatch(...runs) ? labels.text.samePhysical : labels.text.differentPhysical;
    $('outcomes').replaceChildren(...runs.map(outcomeCard));
    $('aggregate-body').replaceChildren(...runs.map(aggregateRow));
    $('sources').replaceChildren(...runs.map(run => element('p', `${controllerName(run.id)} · ${run.source}\nSHA-256 ${run.sha256}`, 'source-line')));
    const markers = new Map();
    runs.forEach(run => run.frames.filter(frame => frame.disturbance).forEach(frame => {
      markers.set(`${frame.t1.toFixed(6)}_${frame.label}`, frame);
    }));
    const events = [...markers.values()].sort((a, b) => a.t1 - b.t1).map(frame => {
      const button = element('button', `${number(frame.t1, 1)} s · ${frame.label}`);
      button.addEventListener('click', () => { setPlaying(false); time = frame.t1; render(); });
      return button;
    });
    $('event-markers').replaceChildren(...(events.length ? events : [element('span', labels.text.noEvents)]));
    resizeCanvas();
    render();
  }

  function outcomeCard(run) {
    const value = run.outcome;
    const card = element('article', undefined, 'outcome-card');
    const title = element('div', undefined, 'outcome-title');
    title.append(element('span', controllerName(run.id)), element('span', value.success ? labels.text.complete : labels.text.failed,
      value.success ? 'status-success' : 'status-failed'));
    const metrics = element('dl', undefined, 'metrics');
    const values = [[labels.ui.duration, value.elapsed_s, labels.ui.seconds], [labels.ui.travel, value.travel_cm, labels.ui.cm],
      [studyId === 'moving' ? labels.ui.silkChord : labels.ui.actorSilk, value.silk_cm, labels.ui.cm],
      [labels.ui.planning, value.planning_s == null ? null : value.planning_s * 1000, labels.ui.ms], [labels.ui.methodCalls, value.method_calls, '', 0]];
    values.forEach(([label, amount, unit, digits]) => {
      const block = element('div');
      const detail = element('dd', number(amount, digits ?? 2));
      detail.append(element('small', ` ${unit}`));
      block.append(element('dt', label), detail);
      metrics.append(block);
    });
    card.append(title, metrics);
    if (value.reason) card.append(element('p', `${labels.ui.failure}: ${value.reason}`, 'note status-failed'));
    if (value.event_fired === false && selectedCase.scenario !== 'clean') card.append(element('p', labels.text.noExposure, 'note'));
    if (value.donor_silk_cm) card.append(element('p', `${number(value.donor_silk_cm)} ${labels.ui.cm} ${labels.ui.donorSilk}. ${labels.text.donor}`, 'note'));
    return card;
  }

  function aggregateRow(run) {
    const stats = run.aggregate;
    const tr = element('tr');
    [controllerName(run.id), `${stats.successes} / ${stats.n}`, number(stats.means.elapsed_s), number(stats.means.travel_cm),
      number(stats.means.silk_cm), number(stats.means.planning_s == null ? null : stats.means.planning_s * 1000)]
      .forEach(value => tr.append(element('td', value)));
    return tr;
  }

  function resizeCanvas() {
    if (recorder) return;
    const narrowPair = matchMedia('(max-width: 800px)').matches && selectedRuns().length === 2;
    canvas.width = narrowPair ? FORMAT.mobileWidth : FORMAT.width;
    canvas.height = narrowPair ? FORMAT.mobileHeight : FORMAT.height;
  }

  function text(value, x, y, size = 14, color = colors.text, align = 'left') {
    ctx.fillStyle = color;
    ctx.font = `${size}px system-ui, sans-serif`;
    ctx.textAlign = align;
    ctx.fillText(value, x, y);
  }

  function render() {
    if (!selectedCase) return;
    const runs = selectedRuns();
    ctx.fillStyle = colors.bg;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    const stacked = canvas.height > canvas.width;
    const panelWidth = stacked ? canvas.width : canvas.width / runs.length;
    const panelHeight = stacked ? canvas.height / runs.length : canvas.height;
    runs.forEach((run, index) => drawRun(run, stacked ? 0 : index * panelWidth, stacked ? index * panelHeight : 0,
      panelWidth, panelHeight, index));
    $('clock').value = `${number(time, 1)} / ${number(replay.duration(runs), 1)} ${labels.ui.seconds}`;
    $('timeline').value = time;
    $('timeline').setAttribute('aria-valuetext', `${number(time, 1)} simulated seconds`);
    if (recorder) $('recording-progress').textContent = `${labels.text.recording} ${number(time, 1)} / ${number(replay.duration(runs), 1)} s`;
  }

  function drawRun(run, x, y, width, height, index) {
    ctx.save();
    ctx.beginPath(); ctx.rect(x, y, width, height); ctx.clip();
    const sample = replay.sample(run, time);
    const tone = index === 0 ? colors.accent : colors.radius;
    const config = selectedCase.config;
    const amplitude = config.amplitude_cm;
    const modelWidth = config.width_cm || 30;
    const modelHeight = config.height_cm || 30;
    const extent = modelWidth + amplitude * 2 + 4;
    const scale = Math.min((width - 90) / extent, (height - 220) / (modelHeight + 4));
    const originX = x + width / 2 - modelWidth * scale / 2;
    const originY = y + 128 + (height - 220 - modelHeight * scale) / 2;
    const point = coordinate => {
      const [px, py] = coordinate;
      const displacement = amplitude * Math.sin(2 * Math.PI * config.frequency_hz * sample.stamp + selectedCase.phase);
      return [originX + (px + (1 - py / modelHeight) * displacement) * scale, originY + (modelHeight - py) * scale];
    };
    const line = (start, end, color, thickness = 1.5, dash = []) => {
      ctx.strokeStyle = color; ctx.lineWidth = thickness; ctx.setLineDash(dash);
      ctx.beginPath(); ctx.moveTo(...point(start)); ctx.lineTo(...point(end)); ctx.stroke(); ctx.setLineDash([]);
    };
    text(controllerName(run.id), x + 26, y + 33, 18, tone);
    const status = sample.finished ? run.outcome.success ? labels.text.complete : labels.text.failed
      : sample.accepted === false ? `${labels.ui.rejected}: ${sample.label}` : sample.label;
    text(status, x + 26, y + 60, 12, sample.accepted === false || sample.finished && !run.outcome.success ? colors.danger : colors['text-dim']);
    text(`${labels.text.timed} ${number(time, 1)} s`, x + width - 26, y + 33, 11, colors['text-dim'], 'right');
    text(`${labels.text.identity} · SEED ${selectedCase.seed}`, x + width - 26, y + 60, 9, colors['text-dim'], 'right');
    text(`${catalog[studyId].tab} · ${$('speed').value}× ${labels.ui.playback}`, x + 26, y + 84, 11, colors['text-dim']);
    text(conditions(selectedCase), x + 26, y + 103, 10, colors['text-dim']);
    ctx.globalAlpha = .35;
    for (let coordinate = 0; coordinate <= modelWidth; coordinate += 5) line([coordinate, 0], [coordinate, modelHeight], colors.border, .7);
    for (let coordinate = 0; coordinate <= modelHeight; coordinate += 5) line([0, coordinate], [modelWidth, coordinate], colors.border, .7);
    ctx.globalAlpha = 1;
    if (studyId === 'moving') {
      [[0, 0], [0, modelHeight], [modelWidth, modelHeight], [modelWidth, 0]].forEach((p, i, points) => line(p, points[(i + 1) % 4], colors.scaffold, 2));
      sample.threads.forEach(frame => line(frame.from, frame.to, phaseColor(frame.kind), 1.6));
      const active = sample.active;
      if (active?.thread) line(active.from, sample.position, phaseColor(active.kind), 2);
    } else {
      run.scaffold.forEach(([a, b]) => line(run.nodes[a], run.nodes[b], colors.scaffold, .8, [3, 5]));
      if (sample.state) {
        sample.state.edges.forEach(([a, b, kind]) => line(run.nodes[a], run.nodes[b], kind === 'capture' ? colors.capture : colors.radius, 2.1));
        sample.state.blocked.forEach(([a, b]) => line(run.nodes[a], run.nodes[b], colors.danger, 2.4, [6, 5]));
      }
      Object.entries(run.nodes).forEach(([name, coordinate]) => {
        const [px, py] = point(coordinate);
        const unavailable = sample.state?.unavailable.includes(name);
        ctx.fillStyle = unavailable ? colors.danger : name.startsWith('B') ? colors.scaffold : colors['text-dim'];
        ctx.beginPath(); ctx.arc(px, py, name === 'hub' ? 3.5 : 2.5, 0, Math.PI * 2); ctx.fill();
        if (config.sectors <= 8 || ['hub', 'left', 'right'].includes(name)) text(name, px + 6, py - 7, 10, ctx.fillStyle);
        if (unavailable) { ctx.strokeStyle = colors.danger; ctx.beginPath(); ctx.moveTo(px - 5, py - 5); ctx.lineTo(px + 5, py + 5); ctx.moveTo(px + 5, py - 5); ctx.lineTo(px - 5, py + 5); ctx.stroke(); }
      });
    }
    drawSpider(point(sample.position), tone, sample.active);
    const bottom = y + height - 72;
    text(`${number(sample.stamp, 1)} ${labels.ui.seconds} ${labels.ui.elapsed}`, x + 26, bottom, 15, colors.text);
    text(`${number(sample.finished ? run.outcome.travel_cm : sample.travel, 1)} ${labels.ui.cm} ${labels.ui.travel.toLowerCase()}`, x + 26, bottom + 25, 12, colors['text-dim']);
    text(`${number(run.outcome.planning_s == null ? null : run.outcome.planning_s * 1000)} ${labels.ui.planningTotal}`, x + width - 26, bottom, 12, tone, 'right');
    text(scenarioName(selectedCase.scenario), x + width - 26, bottom + 25, 11, colors['text-dim'], 'right');
    text(studyId === 'moving' ? labels.text.movingGeometry : labels.text.schematic, x + width / 2, y + height - 15, 10, colors['text-dim'], 'center');
    ctx.strokeStyle = colors.border; ctx.strokeRect(x + .5, y + .5, width - 1, height - 1);
    ctx.restore();
  }

  function phaseColor(kind) { return kind === 'capture' ? colors.capture : kind === 'auxiliary' ? colors.auxiliary : colors.radius; }

  function drawSpider(position, tone, active) {
    ctx.save(); ctx.translate(...position);
    if (active) ctx.rotate(Math.atan2(-(active.to[1] - active.from[1]), active.to[0] - active.from[0]) + Math.PI / 2);
    ctx.strokeStyle = tone; ctx.lineWidth = 1.5;
    for (const side of [-1, 1]) {
      for (let leg = 0; leg < 4; leg++) {
        ctx.beginPath(); ctx.moveTo(side * 3, (leg - 1.5) * 3);
        ctx.lineTo(side * (10 + Math.abs(leg - 1.5) * 2), (leg - 1.5) * 7);
        ctx.lineTo(side * 15, (leg - 1.5) * 11); ctx.stroke();
      }
    }
    ctx.fillStyle = tone; ctx.shadowColor = tone; ctx.shadowBlur = 10;
    ctx.beginPath(); ctx.ellipse(0, 3, 5, 7, 0, 0, 2 * Math.PI); ctx.fill();
    ctx.beginPath(); ctx.arc(0, -5, 3.5, 0, 2 * Math.PI); ctx.fill();
    ctx.restore();
  }

  function canRecord() {
    return typeof canvas.captureStream === 'function' && typeof MediaRecorder !== 'undefined'
      && FORMAT.mimeTypes.some(type => MediaRecorder.isTypeSupported(type));
  }

  function stopRecording() {
    if (finishTimer !== null) clearTimeout(finishTimer);
    finishTimer = null;
    setPlaying(false);
    if (recorder && recorder.state !== 'inactive') recorder.stop();
  }

  function cleanupRecording() {
    if (stream) stream.getTracks().forEach(track => track.stop());
    recorder = null; stream = null;
    $('stop-export').hidden = true;
    $('export').hidden = false;
    $('recording-progress').hidden = true;
    controls(true);
    $('right-select').disabled = !$('compare-toggle').checked;
    resizeCanvas(); render();
  }

  function startRecording() {
    if (!selectedCase || recorder) return;
    if (!canRecord()) { message(labels.text.unsupported); return; }
    invalidateVideo();
    setPlaying(false);
    time = 0;
    render();
    const parts = [];
    recordingFailed = false;
    recordingInterrupted = false;
    const mimeType = FORMAT.mimeTypes.find(type => MediaRecorder.isTypeSupported(type));
    try {
      stream = canvas.captureStream(FORMAT.fps);
      recorder = new MediaRecorder(stream, {mimeType, videoBitsPerSecond: FORMAT.bitsPerSecond});
      const recording = recorder;
      const filename = [labels.text.filePrefix, studyId, selectedCase.id, `seed${selectedCase.seed}`, ...selectedRuns().map(run => run.id), `${$('speed').value}x`].join('-');
      recorder.ondataavailable = event => { if (event.data.size) parts.push(event.data); };
      recorder.onerror = () => { recordingFailed = true; message(labels.text.recordingError); stopRecording(); };
      recorder.onstop = () => {
        if (recorder !== recording) return;
        if (!recordingFailed) {
          const blob = new Blob(parts, {type: recording.mimeType});
          if (blob.size) {
            videoUrl = URL.createObjectURL(blob);
            const videoName = `${filename}.${recording.mimeType.includes('mp4') ? 'mp4' : 'webm'}`;
            const link = element('a', labels.text.download, 'text-link');
            link.id = 'video-download'; link.href = videoUrl; link.download = videoName;
            $('message').replaceChildren(document.createTextNode(`${recordingInterrupted ? labels.text.interrupted : labels.text.exported} `), link);
          } else message(labels.text.emptyVideo);
        }
        cleanupRecording();
      };
      controls(false);
      $('export').hidden = true;
      $('stop-export').hidden = false;
      $('recording-progress').hidden = false;
      message(labels.text.recording);
      recorder.start();
      setPlaying(true);
    } catch {
      setPlaying(false);
      if (recorder && recorder.state !== 'inactive') { recordingFailed = true; recorder.stop(); }
      cleanupRecording();
      message(labels.text.recordingError);
    }
  }

  for (const [id, info] of Object.entries(catalog)) {
    const tab = element('button', info.tab);
    tab.id = `tab-${id}`; tab.dataset.study = id;
    tab.setAttribute('role', 'tab'); tab.setAttribute('aria-controls', 'study-panel');
    tab.addEventListener('click', () => { if (location.hash === `#${id}`) selectStudy(id); else location.hash = id; });
    tab.addEventListener('keydown', event => {
      const tabs = [...$('study-tabs').children];
      let target = null;
      if (event.key === 'ArrowRight') target = tabs[(tabs.indexOf(tab) + 1) % tabs.length];
      if (event.key === 'ArrowLeft') target = tabs[(tabs.indexOf(tab) + tabs.length - 1) % tabs.length];
      if (event.key === 'Home') target = tabs[0];
      if (event.key === 'End') target = tabs.at(-1);
      if (target) { event.preventDefault(); target.focus(); target.click(); }
    });
    $('study-tabs').append(tab);
  }
  $('scenario-select').addEventListener('change', fillCases);
  $('case-select').addEventListener('change', selectCase);
  ['left-select', 'right-select', 'compare-toggle'].forEach(id => $(id).addEventListener('change', updatePair));
  $('play').addEventListener('click', () => { if (time >= replay.duration(selectedRuns())) time = 0; setPlaying(!playing); });
  $('restart').addEventListener('click', () => { setPlaying(false); time = 0; render(); });
  $('timeline').addEventListener('input', () => { setPlaying(false); time = Number($('timeline').value); render(); });
  $('export').addEventListener('click', startRecording);
  $('stop-export').addEventListener('click', stopRecording);
  $('construction-select').addEventListener('change', () => { $('construction-frame').src = $('construction-select').value; });
  window.addEventListener('hashchange', () => { const id = location.hash.slice(1); if (Object.hasOwn(catalog, id)) selectStudy(id); });
  window.addEventListener('resize', () => { resizeCanvas(); render(); });
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) return;
    if (recorder) { recordingInterrupted = true; stopRecording(); }
    else setPlaying(false);
  });
  window.addEventListener('pagehide', () => {
    setPlaying(false);
    if (recorder) { recordingFailed = true; stopRecording(); }
    if (stream) stream.getTracks().forEach(track => track.stop());
    invalidateVideo();
  });
  const initial = location.hash.slice(1);
  selectStudy(Object.hasOwn(catalog, initial) ? initial : studyId);
})();
