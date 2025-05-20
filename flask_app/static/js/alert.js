const alertSocket = io();

// web socket connection
socket.on("new_alert_message", (data) => {
    const timestamp = new Date().toLocaleTimeString();

    const alerts = Array.isArray(data) ? data : [data?.message || "⚠️ Alert received"];

    alerts.forEach(message => {
        const stored = JSON.parse(sessionStorage.getItem("alerts") || "[]");
        stored.unshift({ timestamp, message, isNew: true });
        sessionStorage.setItem("alerts", JSON.stringify(stored.slice(0, 10)));

        const badge = document.getElementById("new-alert-badge");
        const current = parseInt(sessionStorage.getItem("newAlertsCount") || "0");
        sessionStorage.setItem("newAlertsCount", current + 1);
        sessionStorage.setItem("newAlerts", "true");

        if (badge) {
            badge.textContent = current + 1;
            badge.classList.remove("hidden");
        }

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
    });
});

// event listener
document.addEventListener("DOMContentLoaded", () => {
    // on click > close popup
    const closeBtn = document.getElementById("close-alert-box");
    if (closeBtn) {
        closeBtn.addEventListener("click", () => {
            document.getElementById("alert-box").classList.add("hidden");
        });
    }

    // on click > highlights alerts
    const badge = document.getElementById("new-alert-badge");
    if (badge) {
        badge.addEventListener("click", () => {
            const alertList = document.getElementById("alert-list");
            if (!alertList) return;

            const newItems = alertList.querySelectorAll("li[data-new='true']");
            newItems.forEach(el => {
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
            const cleared = saved.map(alert => ({ ...alert, isNew: false }));
            sessionStorage.setItem("alerts", JSON.stringify(cleared));
        });
    }
});