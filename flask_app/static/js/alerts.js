// alerts.js 

export function setupAlertHandling(socket) {
    const closeBtn = document.getElementById("close-alert-box");
    if (closeBtn) {
        closeBtn.addEventListener("click", () => {
            document.getElementById("alert-box").classList.add("hidden");
        });
    }

    const alertBox = document.getElementById("alert-box");
    if (alertBox) {
        alertBox.addEventListener("click", (e) => {
            if (e.target.id === "alert-box") {
                alertBox.classList.add("hidden");
            }
        });
    }

    socket.on("new_alert_message", (data) => {
        const alerts = Array.isArray(data) ? data : [data?.message || "⚠️ Alert received"];

        // Clear previous "isNew" flags
        const old = JSON.parse(sessionStorage.getItem("alerts") || "[]").map(a => ({ ...a, isNew: false }));
        sessionStorage.setItem("alerts", JSON.stringify(old));

        // Save new alerts
        alerts.forEach((message) => {
            const timestamp = new Date().toLocaleTimeString();
            saveAlert(message, timestamp);
            showToastAlert(message, timestamp);
        });

        renderAlertList();
    });

    socket.on("risk_alert_message", (data) => {
        // Clear previous "isNew" flags
        const old = JSON.parse(sessionStorage.getItem("alerts") || "[]").map(a => ({ ...a, isNew: false }));
        sessionStorage.setItem("alerts", JSON.stringify(old));

        const alerts = [];

        if (data && data.patient_id && data.risk_level !== undefined) {
            const fullName = data.first && data.last
                ? `${data.first} ${data.middle ? data.middle + ' ' : ''}${data.last}`
                : `ID ${data.patient_id}`;
            const message = `⚠️ High risk for patient ${fullName} — level: ${data.risk_level}`;
            alerts.push(`[Risk] ${message}`);
        } else {
            const fallback = data?.message || "⚠️ Risk alert received";
            alerts.push(`[Risk] ${fallback}`);
        }

        alerts.forEach((message) => {
            const timestamp = new Date().toLocaleTimeString();
            saveAlert(message, timestamp, "risk");
            showToastAlert(message, timestamp);
        });

        renderAlertList();
    });

    renderAlertList();
}

function saveAlert(message, timestamp, type = "default") {
    const stored = JSON.parse(sessionStorage.getItem("alerts") || "[]");
    const newAlert = { timestamp, message, isNew: true, type };
    const updated = [newAlert, ...stored];
    sessionStorage.setItem("alerts", JSON.stringify(updated.slice(0, 50)));
}

function renderAlertList() {
    const alertList = document.getElementById("alert-list");
    if (!alertList) return;

    const saved = JSON.parse(sessionStorage.getItem("alerts") || "[]");
    if (saved.length === 0) {
        alertList.innerHTML = `<li class="italic text-gray-500">No alerts yet</li>`;
        return;
    }

    alertList.innerHTML = "";
    saved.forEach(({ timestamp, message, isNew, type }) => {
        const li = document.createElement("li");
        const baseClass = "px-2 py-1 rounded text-xs leading-tight break-words flex justify-between items-center gap-2";
        const riskClass = "bg-red-100 text-red-900 border border-red-400";
        const defaultClass = "bg-yellow-100 text-yellow-900 border border-yellow-400";
        li.className = `${type === "risk" ? riskClass : defaultClass} ${baseClass}`;
        li.innerHTML = `
            <span>${timestamp} — ${message}</span>
            ${isNew ? '<span class="ml-2 px-2 py-0.5 text-[10px] bg-red-500 text-white rounded-full">NEW</span>' : ''}
        `;
        alertList.appendChild(li);
    });
}

export function showToastAlert(message, timestamp = "") {
    const container = document.getElementById("alert-container");
    if (!container) return;

    const alertDiv = document.createElement("div");
    const isRisk = message.includes("[Risk]");
    alertDiv.className = `${isRisk ? "bg-red-100 border-red-500 text-red-700" : "bg-yellow-100 border-yellow-500 text-yellow-700"} border-l-4 p-3 rounded shadow-lg max-w-xs animate-fadeInOut`;
    alertDiv.innerHTML = `
        <div class="flex justify-between items-start gap-2">
            <div class="text-sm">
                <strong class="block mb-1">⚠️ Alert</strong>
                <span>${timestamp} — ${message}</span>
            </div>
            <button class="text-yellow-500 hover:text-yellow-700 text-xl leading-none font-bold">&times;</button>
        </div>
    `;

    alertDiv.querySelector("button").addEventListener("click", () => {
        alertDiv.remove();
    });

    container.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.remove();
    }, 6000);
}