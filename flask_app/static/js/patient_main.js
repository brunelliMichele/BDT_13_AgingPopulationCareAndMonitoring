// patient_main.js

// This script handles real-time updates for smart home sensor data on the patient detail page.
// It listens for incoming WebSocket messages and updates the DOM accordingly.

import { io } from "https://cdn.socket.io/4.5.4/socket.io.esm.min.js";
import { setupAlertHandling } from "./alerts.js";

const socket = io("/");

// Sets up a WebSocket listener for smart home data and updates the DOM with sensor and appliance information
function setupSensorUpdates() {
    const userId = document.getElementById("patient-id")?.dataset.id;
    if (!userId) return;

    socket.on("smart_data_message", (msg) => {
        const userId = document.getElementById("patient-id")?.dataset.id;

        for (const key in msg) {
            const entry = msg[key];
            if (!entry || !entry.patient_id || String(entry.patient_id).trim() !== String(userId).trim()) {
                continue;
            }

            const timestamp = entry.timestamp;
            const rooms = entry.data?.rooms;

            document.getElementById("sensor-timestamp").textContent = timestamp;
            const container = document.getElementById("sensor-rooms");
            container.innerHTML = "";

            // Display message if no room data is available
            if (!rooms || Object.keys(rooms).length === 0) {
                container.innerHTML = "<p class='italic text-gray-500'>No room data available.</p>";
                return;
            }

            for (const room in rooms) {
                const r = rooms[room];
                // Filter and format active appliances
                const appliances = Object.entries(r.appliances || {})
                    .filter(([_, info]) => info.Status === "On")
                    .map(([name, info]) => `⚙️ ${name} (${info["Duration (min)"]} min)`)
                    .join(", ");

                const applianceContent = appliances || "<span class='text-gray-400 italic'>No devices active</span>";

                container.innerHTML += `
                    <div class="border border-teal-100 p-3 rounded-lg bg-teal-50 min-h-[120px] overflow-hidden text-sm leading-snug space-y-1">
                        <h4 class="font-semibold text-teal-600">${room}</h4>
                        <p>🌡️ Temp: ${r.temperature}°C &nbsp;&nbsp; 💧 Humidity: ${r.humidity}%</p>
                        <p>🔌 Active: ${applianceContent}</p>
                    </div>
                `;
            }
        }
    });
}

// Initialize real-time updates and table sorting once the page has fully loaded
document.addEventListener("DOMContentLoaded", () => {
    setupSensorUpdates();
    setupAlertHandling(socket);

    const table = document.querySelector("table");
    if (table) {
        const sorter = new Tablesort(table);

        table.addEventListener("afterSort", function (e) {
            // Remove all existing sort icons
            document.querySelectorAll("span.sort-indicator").forEach((el) => el.remove());

            // Tablesort adds class 'asc' or 'desc' to the sorted header
            const sortedTh = table.querySelector("th[aria-sort='ascending'], th[aria-sort='descending']");
            
            if (sortedTh) {
                const direction = sortedTh.getAttribute("aria-sort") === "ascending" ? "asc" : "desc";

                const icon = document.createElement("span");
                icon.className = "sort-indicator text-xs ml-1";
                icon.textContent = direction === "asc" ? "↑" : "↓";

                const flexContainer = sortedTh.querySelector("div.flex");
                    flexContainer.appendChild(icon);
            }
        });
    }
});