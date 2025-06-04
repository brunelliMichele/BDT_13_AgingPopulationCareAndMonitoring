// main.js

import { io } from "https://cdn.socket.io/4.5.4/socket.io.esm.min.js";
import { setupAlertHandling } from "./alerts.js";
import { updateUI, setupUIEvents } from "./ui.js";
import { initMap } from "./map.js";

const socket = io("/");

document.addEventListener("DOMContentLoaded", () => {
    initMap();
    setupAlertHandling(socket);
    setupUIEvents();
    updateUI();
});