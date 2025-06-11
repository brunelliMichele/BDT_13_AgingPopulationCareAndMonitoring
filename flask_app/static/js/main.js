// main.js

// Entry point for the frontend JavaScript. 
// Initializes map, alert handling, and user interface updates once the DOM is fully loaded.

import { io } from "https://cdn.socket.io/4.5.4/socket.io.esm.min.js"; // Import Socket.IO client for real-time communication
import { setupAlertHandling } from "./alerts.js"; // Handles incoming alerts and displays them
import { updateUI, setupUIEvents } from "./ui.js"; // Updates the interface and sets up event listeners
import { initMap } from "./map.js"; // Initializes the Leaflet map

const socket = io("/");

// Wait for the DOM to be fully loaded before initializing components
document.addEventListener("DOMContentLoaded", () => {
    initMap();
    setupAlertHandling(socket);
    setupUIEvents();
    updateUI();
});