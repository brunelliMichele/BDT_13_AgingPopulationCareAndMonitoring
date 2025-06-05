// alerts.js 

export function setupAlertHandling(socket) {
    const closeBtn = document.getElementById("close-alert-box");
    const alertBox = document.getElementById("alert-box");

    if (closeBtn) {
        closeBtn.addEventListener("click", () => {
            alertBox?.classList.add("hidden");
        });
    }

    socket.on("new_alert_message", (data) => {
        handleIncomingAlert("default", data);
    });

    socket.on("risk_alert_message", (data) => {
        handleIncomingAlert("risk", data);
    });

    renderAlertList();
}

function handleIncomingAlert(type, data) {
    const alerts = Array.isArray(data)
        ? data.map((msg) => {
            const message = typeof msg === "string" ? msg : msg.message || "⚠️ Alert received";
            const patient_id = typeof msg === "object" ? msg.patient_id : null;
            return {
                message,
                patient_id,
                isNew: true,
                type
            };
        })
        : [{
            message: data.message || `⚠️ ${type === "risk" ? "Risk" : "Alert"} received`,
            patient_id: data.patient_id,
            isNew: true,
            type
        }];

    const old = JSON.parse(sessionStorage.getItem("alerts") || "[]").map(a => ({ ...a, isNew: false }));

    const newAlerts = alerts.map(({ message, patient_id, isNew, type }) => {
        const timestamp = new Date().toLocaleTimeString();
        showToastAlert(message, timestamp, { patient_id, type });
        return { timestamp, message, isNew, type, patientId: patient_id };
    });

    const updated = [...newAlerts, ...old].slice(0, 50);
    sessionStorage.setItem("alerts", JSON.stringify(updated));

    renderAlertList();
}

function saveAlert(message, timestamp, type = "default", patientId = null, isNew = true) {
    const stored = JSON.parse(sessionStorage.getItem("alerts") || "[]");
    const newAlert = { timestamp, message, isNew, type, patientId };
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
    saved.forEach(({ timestamp, message, isNew, type, patientId }) => {
        const li = document.createElement("li");
        const baseClass = "px-2 py-1 rounded text-xs leading-tight break-words flex justify-between items-center gap-2";
        const riskClass = "bg-red-100 text-red-900 border border-red-400";
        const defaultClass = "bg-yellow-100 text-yellow-900 border border-yellow-400";
        li.className = `${type === "risk" ? riskClass : defaultClass} ${baseClass}`;

        if (patientId) {
            li.classList.add("cursor-pointer");
            li.addEventListener("click", () => {
                window.location.href = `/patient/${patientId}`;
            });
        }

        li.innerHTML = `
            <span>${timestamp} — ${message}</span>
            ${isNew ? '<span class="ml-2 px-2 py-0.5 text-[10px] bg-red-500 text-white rounded-full">NEW</span>' : ''}
        `;
        alertList.appendChild(li);
    });
}

export function showToastAlert(message, timestamp = "", messageData = {}) {
    let container = document.getElementById("alert-container");
    let wrapper = document.getElementById("alert-wrapper");

    if (!wrapper) {
        wrapper = document.createElement("div");
        wrapper.id = "alert-wrapper";
        wrapper.className = "fixed top-2 right-6 z-50 flex flex-col items-end gap-2";
        document.body.appendChild(wrapper);
    }

    if (!container) {
        container = document.createElement("div");
        container.id = "alert-container";
        container.className = "flex flex-col gap-2";
        wrapper.appendChild(container);
    }

    const alertDiv = document.createElement("div");
    const isRisk = messageData?.type === "risk" || message.includes("[Risk]");
    alertDiv.className = `${isRisk ? "bg-red-100 border-red-500 text-red-700" : "bg-yellow-100 border-yellow-500 text-yellow-700"} border-l-4 p-3 rounded shadow-lg max-w-xs animate-fadeInOut`;

    alertDiv.innerHTML = `
        <div class="flex justify-between items-start gap-2">
            <div class="text-sm">
                <strong class="block mb-1">⚠️ Alert</strong>
                <span>${timestamp} — ${message}</span>
            </div>
            <button class="bg-white border border-gray-300 hover:border-gray-400 rounded px-2 py-0.5 text-gray-600 hover:text-black text-base font-semibold shadow-sm transition" aria-label="Close alert">&times;</button>
        </div>
    `;

    const patientId = messageData.patient_id || (message.match(/\(ID: ([\w-]+)\)/)?.[1] ?? null);

    if (patientId) {
        alertDiv.classList.add("cursor-pointer");
        alertDiv.addEventListener("click", () => {
            window.location.href = `/patient/${patientId}`;
        });
    }

    alertDiv.querySelector("button").addEventListener("click", (e) => {
        e.stopPropagation();
        alertDiv.remove();
    });

    container.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.remove();
        showCloseAllButton();
    }, 6000);

    const observer = new MutationObserver(() => {
        showCloseAllButton();
    });
    observer.observe(container, { childList: true });
}

// Dynamically create and insert the "Close all" button when there are alerts
function showCloseAllButton() {
    let wrapper = document.getElementById("alert-wrapper");
    let container = document.getElementById("alert-container");
    if (!wrapper || !container) return;

    // Only show button if there are visible alerts
    const hasAlerts = container.children.length > 0;
    let closeAllBtn = document.getElementById("close-all-alerts");

    // Remove button if no alerts
    if (!hasAlerts && closeAllBtn) {
        closeAllBtn.remove();
        return;
    }

    // Add button if alerts exist and button not present
    if (hasAlerts && !closeAllBtn) {
        closeAllBtn = document.createElement("button");
        closeAllBtn.id = "close-all-alerts";
        closeAllBtn.className = "bg-white text-sm border border-gray-300 hover:border-gray-400 px-3 py-1 rounded shadow text-gray-600 hover:text-black transition mb-1";
        closeAllBtn.textContent = "✖ Close all";
        closeAllBtn.addEventListener("click", () => {
            container.innerHTML = "";
            showCloseAllButton();
        });
        // Insert button at the top of the wrapper
        wrapper.insertBefore(closeAllBtn, wrapper.firstChild);
    }
}