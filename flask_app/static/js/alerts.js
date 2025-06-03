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

    const badge = document.getElementById("new-alert-badge");
    if (badge) {
        badge.addEventListener("click", highlightNewAlerts);
    }

    socket.on("new_alert_message", (data) => {
        console.log("🚨 ALERT RECEIVED", data);
        const alerts = Array.isArray(data) ? data : [data?.message || "⚠️ Alert received"];
        alerts.forEach((message) => {
            const timestamp = new Date().toLocaleTimeString();
            saveAlert(message, timestamp);
            updateBadge();
            showPopup(message, timestamp);
        });
        renderAlertList();
    });

    socket.on("risk_alert_message", (data) => {
        console.log("📈 RISK ALERT RAW DATA", JSON.stringify(data));

        if (data && data.patient_id && data.risk_level !== undefined) {
            const fullName = data.first && data.last
                ? `${data.first} ${data.middle ? data.middle + ' ' : ''}${data.last}`
                : `ID ${data.patient_id}`;
            const message = `⚠️ High risk for patient ${fullName} — level: ${data.risk_level}`;
            const timestamp = new Date().toLocaleTimeString();
            saveAlert(`[Risk] ${message}`, timestamp, "risk");
            updateBadge();
            showPopup(`[Risk] ${message}`, timestamp);
        } else {
            const fallback = data?.message || "⚠️ Risk alert received";
            const timestamp = new Date().toLocaleTimeString();
            saveAlert(`[Risk] ${fallback}`, timestamp, "risk");
            updateBadge();
            showPopup(`[Risk] ${fallback}`, timestamp);
        }

        renderAlertList();
    });

    renderAlertList();
    updateBadge();
}

function saveAlert(message, timestamp, type = "default") {
    const stored = JSON.parse(sessionStorage.getItem("alerts") || "[]");
    stored.unshift({ timestamp, message, isNew: true, type });
    sessionStorage.setItem("alerts", JSON.stringify(stored.slice(0, 50)));

    const count = parseInt(sessionStorage.getItem("newAlertsCount") || "0") + 1;
    sessionStorage.setItem("newAlertsCount", count);
    sessionStorage.setItem("newAlerts", "true");
}

function updateBadge() {
    const badge = document.getElementById("new-alert-badge");
    const count = parseInt(sessionStorage.getItem("newAlertsCount") || "0");
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.classList.remove("hidden");
        } else {
            badge.classList.add("hidden");
        }
    }
}

function showPopup(message, timestamp) {
    const alertBox = document.getElementById("alert-box");
    const alertElement = document.getElementById("alert");
    const alertContent = document.getElementById("alert-content");

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
}

function highlightNewAlerts() {
    const alertList = document.getElementById("alert-list");
    const badge = document.getElementById("new-alert-badge");
    if (!alertList || !badge) return;

    const newItems = alertList.querySelectorAll("li[data-new='true']");
    newItems.forEach((el) => {
        el.classList.add("bg-yellow-200", "border-2", "border-yellow-500");
        setTimeout(() => {
            el.classList.remove("bg-yellow-200", "border-2", "border-yellow-500");
        }, 3000);
        el.removeAttribute("data-new");
    });

    badge.textContent = "0";
    badge.classList.add("hidden");
    sessionStorage.setItem("newAlertsCount", "0");
    sessionStorage.removeItem("newAlerts");

    const saved = JSON.parse(sessionStorage.getItem("alerts") || "[]");
    const cleared = saved.map((a) => ({ ...a, isNew: false }));
    sessionStorage.setItem("alerts", JSON.stringify(cleared));
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
        li.className =
            type === "risk"
                ? "bg-yellow-100 text-yellow-900 border border-yellow-400 px-2 py-1 rounded text-xs leading-tight break-words"
                : "bg-rose-100 text-rose-700 border border-rose-200 px-2 py-1 rounded text-xs leading-tight break-words";
        li.title = `${timestamp} — ${message}`;
        li.textContent = `${timestamp} — ${message}`;
        if (isNew) li.dataset.new = "true";
        alertList.appendChild(li);
    });
}