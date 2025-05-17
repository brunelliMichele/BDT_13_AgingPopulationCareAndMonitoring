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
            <div class="border border-teal-100 p-3 rounded-lg bg-teal-50 min-h-[120px] text-sm leading-relaxed space-y-1">
                <h4 class="font-semibold text-teal-600">${room}</h4>
                <p>🌡️ Temp: ${r.temperature}°C &nbsp;&nbsp; 💧 Humidity: ${r.humidity}%</p>
                <p>🔌 Active: ${applianceContent}</p>
            </div>
        `;
    }
});


document.getElementById("close-alert-box").addEventListener("click", () => {
    document.getElementById("alert-box").classList.add("hidden");
});