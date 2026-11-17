/* Runs only in the temporary browser-check copy, never in the application. */
(async () => {
  const report = document.createElement('pre');
  report.id = 'browser-check-results';
  document.body.prepend(report);
  const checks = [];
  const $ = id => document.getElementById(id);
  function assert(condition, description) {
    if (!condition) throw new Error(description);
    checks.push(description);
  }
  async function until(predicate) {
    for (let attempt = 0; attempt < 700; attempt++) {
      if (predicate()) return;
      await new Promise(resolve => setTimeout(resolve, 20));
    }
    throw new Error('Timed out waiting for browser state');
  }
  async function study(id) {
    location.hash = id;
    await until(() => $('tab-' + id)?.getAttribute('aria-selected') === 'true' &&
      (id === 'construction' || $('outcomes').children.length > 0 && $('study-panel').getAttribute('aria-busy') === 'false'));
  }
  function change(id, value) {
    $(id).value = value;
    $(id).dispatchEvent(new Event('change', {bubbles: true}));
  }
  try {
    await until(() => $('outcomes').children.length === 2);
    assert(document.querySelectorAll('[role=tab]').length === 5, 'Five keyboard-operable experiment tabs');
    assert($('left-select').value === 'state_rules' && $('right-select').value === 'retained_htn', 'Default E1 comparison selects state rules and retained HTN');
    assert($('pair-verdict').textContent.includes('match'), 'E1 physical tie stays visible');
    assert($('event-markers').querySelector('button'), 'Damage intervention has a jump marker');
    $('event-markers').querySelector('button').click();
    assert(Number($('timeline').value) > 0, 'Event jump seeks the simulation clock');
    const e1 = window.EXPERIMENT_STUDIES.e1;
    const savedCase = e1.cases.find(item => item.id === $('case-select').value);
    const first = savedCase.runs.find(run => run.id === 'state_rules');
    const history = savedCase.runs.find(run => run.id === 'history');
    const clock = window.ExperimentReplay.duration([first, history]);
    assert(window.ExperimentReplay.sample(history, clock).finished, 'Shorter failed replay holds its final state at the shared later time');
    const intervention = first.frames.find(frame => frame.kind === 'intervention');
    assert(JSON.stringify(window.ExperimentReplay.sample(first, intervention.t1).state) === JSON.stringify(first.states[intervention.state]), 'Zero-duration damage applies at its exact recorded timestamp');
    change('right-select', 'history');
    assert($('pair-verdict').textContent.includes('differ'), 'Failed cached history is distinguished from capable recovery');
    $('compare-toggle').click();
    assert($('outcomes').children.length === 1 && $('right-field').hidden, 'Single-run mode updates canvas selection and accessible outcomes');
    $('compare-toggle').click();
    change('scenario-select', 'transfer_partial');
    assert($('outcomes').textContent.includes('donor silk'), 'Transfer preserves donor-versus-actor silk labeling');
    const appendScript = document.head.append;
    document.head.append = function(node) {
      if (node.tagName === 'SCRIPT' && node.src.endsWith('/moving.js')) setTimeout(() => node.dispatchEvent(new Event('error')), 0);
      else appendScript.call(this, node);
    };
    location.hash = 'moving';
    await until(() => $('message').textContent.includes('could not be loaded'));
    assert($('play').disabled && !$('tab-moving').disabled, 'Missing bundle gives an explicit error with safe disabled replay controls');
    document.head.append = appendScript;
    $('tab-moving').click();
    await study('moving');
    assert($('left-select').value === 'ipyhop_fresh' && $('right-select').value === 'ipyhop_retained', 'Moving-support comparison uses matched fresh and retained engines');
    assert($('aggregate-silk-label').textContent.includes('chord'), 'Moving-support silk metric is labeled chord length');
    const movingMiss = window.EXPERIMENT_STUDIES.moving.cases.find(item => item.scenario === 'transient_miss').runs[0];
    const rejected = movingMiss.frames.find(frame => !frame.accepted);
    assert(window.ExperimentReplay.sample(movingMiss, (rejected.t0 + rejected.t1) / 2).accepted === false, 'Rejected attachments remain explicit in the replay state');
    let delayedScript;
    document.head.append = function(node) {
      if (node.tagName === 'SCRIPT' && node.src.endsWith('/recovery.js')) delayedScript = node;
      else appendScript.call(this, node);
    };
    location.hash = 'recovery';
    await until(() => delayedScript);
    await study('construction');
    assert($('study-panel').getAttribute('aria-busy') === 'false', 'Switching to construction during a pending load clears the accessible busy state');
    document.head.append = appendScript;
    appendScript.call(document.head, delayedScript);
    await until(() => window.EXPERIMENT_STUDIES.recovery);
    assert($('tab-construction').getAttribute('aria-selected') === 'true' && !$('construction-panel').hidden, 'Stale bundle load cannot replace the newly selected study');
    await study('recovery');
    change('scenario-select', 'unreachable');
    assert($('outcomes').textContent.includes('Failed'), 'Unreachable routes retain recorded failure outcomes');
    assert($('aggregate-body').textContent.includes('—'), 'Empty successful physical means show unavailable, not zero');
    await study('expanded');
    const resource = [...$('case-select').options].find(option => option.textContent.includes('151 cm stock'));
    assert(resource, 'Expanded demos include an unexposed resource-boundary case');
    change('case-select', resource.value);
    assert($('outcomes').textContent.includes('Intervention not reached'), 'Unexposed failures are explicitly labeled');
    await study('construction');
    assert(!$('construction-panel').hidden && $('construction-frame').getAttribute('src') === 'index_updated.html', 'Existing construction renderer remains available');
    await study('e1');
    assert(!$('construction-frame').getAttribute('src'), 'Leaving construction unloads its background animation');
    $('tab-e1').dispatchEvent(new KeyboardEvent('keydown', {key: 'Home', bubbles: true}));
    await study('construction');
    assert($('tab-construction').tabIndex === 0, 'Home key activates the first tab with roving focus');
    await study('e1');
    // Failure injection checks the real UI recovery path, not a mirrored implementation.
    const NativeRecorder = window.MediaRecorder;
    class FailingRecorder {
      static isTypeSupported() { return true; }
      constructor() { throw new Error('Injected encoder failure'); }
    }
    window.MediaRecorder = FailingRecorder;
    $('export').disabled = false;
    $('export').click();
    assert(!$('play').disabled && !$('case-select').disabled && $('message').textContent.includes('failed'), 'Encoder startup failure restores controls and explains the error');
    window.MediaRecorder = undefined;
    change('left-select', $('left-select').value);
    assert($('export').disabled, 'Unsupported video recording disables export without breaking replay');
    window.MediaRecorder = NativeRecorder;
    change('scenario-select', 'intact');
    change('speed', '100');
    if (NativeRecorder && HTMLCanvasElement.prototype.captureStream) {
      $('export').click();
      assert($('play').disabled && !$('stop-export').hidden, 'Native export locks selections while capturing');
      await until(() => $('video-download'));
      const blob = await (await fetch($('video-download').href)).blob();
      assert(blob.size > 1000, 'Native recording produces a nonempty downloadable video');
      const video = document.createElement('video');
      video.src = $('video-download').href;
      await until(() => video.readyState >= 1);
      assert(video.videoWidth === $('replay-canvas').width && video.videoHeight === $('replay-canvas').height, 'Exported video decodes at the replay canvas dimensions');
      assert(!$('play').disabled && $('stop-export').hidden, 'Successful recording restores playback controls');
    }
    change('scenario-select', 'damage_single');
    $('event-markers').querySelector('button').click();
    assert(document.documentElement.scrollWidth <= innerWidth + 1, 'Page fits the viewport without horizontal page overflow');
    report.dataset.status = 'passed';
    report.textContent = JSON.stringify({status: 'passed', checks}, null, 2);
  } catch (error) {
    report.dataset.status = 'failed';
    report.textContent = JSON.stringify({status: 'failed', error: error.message, checks}, null, 2);
  }
})();
