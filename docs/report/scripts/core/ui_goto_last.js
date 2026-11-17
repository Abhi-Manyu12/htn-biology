// Drive the interactive visualiser to its final step (all actions applied) before capture.
pause && pause();
goToStep(PLAN_DATA.total_steps - 1, true);
draw();
