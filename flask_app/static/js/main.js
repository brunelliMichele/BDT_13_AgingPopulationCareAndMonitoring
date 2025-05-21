// main.js

import { setupAlertHandling } from "./alerts.js";
import { updateUI, setupUIEvents } from "./ui.js";
import { initMap } from "./map.js";

document.addEventListener("DOMContentLoaded", () => {
    initMap();
    setupAlertHandling();
    setupUIEvents();
    updateUI();
});