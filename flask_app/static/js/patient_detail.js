// !!-- WEB SOCKET SECTION --!!
const socket = io();

socket.on('smart_data_message', function (msg) {
    const userKey = "user_001" // for development only

    if (!(userKey in msg)) return;

    const data = msg[userKey];
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


socket.on("new_alert_message", (data) => {
    const alertBox = document.getElementById("alert-box");
    const alertElement = document.getElementById("alert");
    const alertContent = document.getElementById("alert-content");

    const timestamp = new Date().toLocaleTimeString();
    const message = typeof data === "string" ? data : (data?.message || "⚠️ Alert received");

    // save the sessionStorage
    const storedAlerts = JSON.parse(sessionStorage.getItem("alerts") || "[]");
    storedAlerts.unshift({ timestamp, message, isNew: true });
    sessionStorage.setItem("alerts", JSON.stringify(storedAlerts.slice(0, 10)));
    const currentCount = parseInt(sessionStorage.getItem("newAlertsCount") || "0");
    sessionStorage.setItem("newAlertsCount", (currentCount + 1).toString());
    sessionStorage.setItem("newAlerts", "true");

    // shows Badge (if present)
    const badge = document.getElementById("new-alert-badge");
    if (badge) {
        let count = parseInt(badge.textContent) || 0;
        count++;
        badge.textContent = count;
        badge.classList.remove("hidden");
    }

    // shows Pop-up
    if (alertBox && alertElement && alertContent) {
        alertBox.classList.remove("hidden");
        alertElement.textContent = `${timestamp} — ${message}`;
        alertContent.classList.remove("scale-95", "opacity-0");
        alertContent.classList.add("scale-100", "opacity-100");

        setTimeout(() => {
            alertBox.classList.add("hidden");
            alertContent.classList.remove("scale-100", "opacity-100");
            alertContent.classList.add("scale-95", "opacity-0");
        }, 10000);
    }
});

document.getElementById("close-alert-box").addEventListener("click", () => {
    document.getElementById("alert-box").classList.add("hidden");
});
