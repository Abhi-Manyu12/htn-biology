// Drive index_updated.html to the last capture-spiral step (just before mark_web_complete), where the
// page still colours threads by type (at the final step it hides the auxiliary spiral and draws plain silk).
pause && pause();
let k = PLAN_DATA.steps.findIndex(s => s.name === 'mark_capture_spiral_done');
goToStep(k, true);
draw();
