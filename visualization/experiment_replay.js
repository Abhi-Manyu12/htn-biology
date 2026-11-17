/* Pure time/state selection shared by playback, capture and browser checks. */
window.ExperimentReplay = (() => {
  function sample(run, time) {
    const stamp = Math.min(time, run.outcome.elapsed_s);
    let position = run.initial;
    let state = run.states[0] || null;
    let label = window.EXPERIMENT_LABELS.text.ready;
    let active = null;
    let travel = 0;
    let accepted = true;
    const threads = [];
    for (const frame of run.frames) {
      if (frame.t1 <= stamp) {
        position = frame.to;
        if (frame.state !== undefined) state = run.states[frame.state];
        label = frame.label;
        accepted = frame.accepted;
        travel = frame.travel;
        if (frame.thread) threads.push(frame);
      } else if (frame.t0 <= stamp && stamp < frame.t1) {
        const progress = (stamp - frame.t0) / (frame.t1 - frame.t0);
        position = frame.from.map((v, index) => v + (frame.to[index] - v) * progress);
        if (frame.before !== undefined) state = run.states[frame.before];
        label = frame.label;
        accepted = frame.accepted;
        active = frame;
        break;
      } else if (frame.t0 > stamp) break;
    }
    return {stamp, position, state, label, active, threads, travel, accepted, finished: time >= run.outcome.elapsed_s};
  }

  function physicalMatch(left, right) {
    return ['success', 'elapsed_s', 'travel_cm', 'silk_cm'].every(key => left.outcome[key] === right.outcome[key]);
  }

  function duration(runs) { return Math.max(...runs.map(run => run.outcome.elapsed_s), 0); }

  return {sample, physicalMatch, duration};
})();
