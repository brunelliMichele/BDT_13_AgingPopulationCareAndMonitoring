const alertSocket = io();

// web socket connection
alertSocket.on("new_alert_message", (data) => {
    const timestamp = new Date().toLocaleTimeString();
    const message = typeof data === "string" ? data : (data?.message || "⚠️ Alert received");

    // save in sessionStorage
    const storedAlerts = JSON.parse(sessionStorage.getItem("alerts") || "[]");
    storedAlerts.unshift({ timestamp, message, isNew: true });
    sessionStorage.setItem("alerts", JSON.stringify(storedAlerts.slice(0, 10)));

    const currentCount = parseInt(sessionStorage.getItem("newAlertsCount") || "0");
    sessionStorage.setItem("newAlertsCount", (currentCount + 1).toString());
    sessionStorage.setItem("newAlerts", "true");

    // update badge if exists
    const badge = document.getElementById("new-alert-badge");
    if (badge) {
        const count = parseInt(sessionStorage.getItem("newAlertsCount") || "0");
        badge.textContent = count;
        badge.classList.remove("hidden");
    }

    // shows alert popup
    const alerBox = document.getElementById("alert-box");
    const alertElement = document.getElementById("alert");
    const alertContent = document.getElementById("alert-content");

    if (alerBox && alertElement && alertContent) {
        alerBox.classList.remove("hidden");
        alertElement.textContent = `${timestamp} — ${message}`;
        alertContent.classList.remove("scale-95", "opacity-0");
        alertContent.classList.add("scale-100", "opacity-100");

        // automatic close popup after 10 seconds
        setTimeout(() => {
            alerBox.classList.add("hidden");
            alertContent.classList.remove("scale-100", "opacity-100");
            alertContent.classList.add("scale-95", "opacity-0");
        }, 10000);
    }
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