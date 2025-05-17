const socket = io();

socket.on('connect', () => {
    console.log('✅ Connected to server');
});

socket.on('kafka_message', function (msg) {
    /* const patientId = document.getElementById("patient-id").dataset.id;
    const userKey = "user_" + patientId; */

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


socket.on("new_alert", (data) => {
    const alertBox = document.getElementById("alert-box");
    const alertElement = document.getElementById("alert");
    const alertContent = document.getElementById("alert-content");

    const timestamp = new Date().toLocaleTimeString();
    const message = typeof data === "string" ? data : (data?.message || "⚠️ Alert received");

    // save in sessionStorage
    if (!document.getElementById("alert-list")) {
        const storedAlerts = JSON.parse(sessionStorage.getItem("alerts") || "[]");
        storedAlerts.unshift({ timestamp, message });
        sessionStorage.setItem("alerts", JSON.stringify(storedAlerts.slice(0, 10)));

        // shows the new alerts in the homepage on the nex visit
        sessionStorage.setItem("newAlerts", "true");
    }

    // shows the badge (if it is presente in the page)
    const badge = document.getElementById("new-alert-badge");
    if (badge && sessionStorage.getItem("newAlerts") === "true") {
        badge.classList.remove("hidden");
    }

    // shows the pop-up
    if (alertBox && alertElement && alertContent) {
        alertBox.classList.remove("hidden");
        alertElement.textContent = `${timestamp} — ${message}`;
        alertContent.classList.remove("scale-95", "opacity-0");
        alertContent.classList.add("scale-100", "opacity-100");

        // automatically close the pop-up after 10 seconds
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
