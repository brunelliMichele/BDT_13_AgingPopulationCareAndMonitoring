// patient_main.js

import { io } from "https://cdn.socket.io/4.5.4/socket.io.esm.min.js";
import { setupAlertHandling } from "./alerts.js";

const socket = io("/");

socket.on("connect", () => {
    console.log("✅ Socket connected");
});

socket.onAny((event, ...args) => {
    console.log("📡 Received event:", event, args);
});

function setupSensorUpdates() {
    const userId = document.getElementById("patient-id")?.dataset.id;
    if (!userId) return;

    socket.on("smart_data_message", (msg) => {
        console.log("💡 smart_data_message", msg);
        if (!(userId in msg)) return;

        const data = msg[userId];
        const timestamp = Object.keys(data)[0];
        const rooms = data[timestamp].rooms;

        document.getElementById("sensor-timestamp").textContent = timestamp;
        const container = document.getElementById("sensor-rooms");
        container.innerHTML = "";

        for (const room in rooms) {
            const r = rooms[room];
            const appliances = Object.entries(r.appliances)
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
    });
}

document.addEventListener("DOMContentLoaded", () => {
    setupSensorUpdates();
    setupAlertHandling(socket);
});