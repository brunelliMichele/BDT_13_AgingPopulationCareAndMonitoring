const patientsData = JSON.parse(document.getElementById("patientsJson").textContent);
const patientsPerPage = 6;
let currentPage = 1;
let filteredPatients = [...patientsData];

const container = document.getElementById("patientsContainer");
const searchInput = document.getElementById("searchInput");
const prevBtn = document.getElementById("prevPage");
const nextBtn = document.getElementById("nextPage");
const pageInfo = document.getElementById("pageInfo");

// function for the patients list
function renderPatients() {
        container.innerHTML = "";
        const start = (currentPage - 1) * patientsPerPage;
        const end = start + patientsPerPage;
        const patientsToShow = filteredPatients.slice(start, end);

        patientsToShow.forEach(p => {
        const div = document.createElement("div");
        div.className = "bg-teal-50 border border-teal-200 p-4 rounded-lg shadow-md";

        div.innerHTML = `
            <h3 class="text-lg font-bold text-teal-700">🧓 ${p.name} ${p.middlename} ${p.surname}</h3>
            <p class="text-gray-700 text-sm"><strong>ID:</strong> ${p.id}</p>
            <p class="text-gray-700 text-sm"><strong>Birth:</strong> ${p.birthdate}</p>
            <p class="text-gray-700 text-sm"><strong>City:</strong> ${p.city}</p>
            <a href="${p.url}" class="text-teal-600 hover:text-teal-800 underline text-sm">View details</a>
        `;

        container.appendChild(div);
    });

    pageInfo.textContent = `Page ${currentPage} of ${Math.ceil(filteredPatients.length / patientsPerPage)}`;
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage >= Math.ceil(filteredPatients.length / patientsPerPage);
}

// function that show only patients for the selected city
function applyFilters() {
    const keyword = searchInput.value.toLowerCase();
    const selectedCity = document.getElementById("city-select").value.toLowerCase();

    filteredPatients = patientsData.filter(p => {
        const nameMatch = p.name.toLowerCase().includes(keyword) ||
                          (p.middlename || "").toLowerCase().includes(keyword) ||
                          p.surname.toLowerCase().includes(keyword);
        const cityMatch = !selectedCity || p.city.toLowerCase() === selectedCity;
        return nameMatch && cityMatch;
    });

    currentPage = 1;
    renderPatients();
}

/* // for handle test alert 
function triggerTestAlert() {
    socket.emit("test_alert", {
        message: "🔥 Test alert triggered manually",
        timestamp: new Date().toLocaleTimeString()
    });
} */


searchInput.addEventListener("input", applyFilters);
document.getElementById("city-select").addEventListener("change", applyFilters);

// event handler for "previous button"
prevBtn.addEventListener("click", () => {
    if (currentPage > 1) {
        currentPage--;
        renderPatients();
    }
});

// event handler for "next button"
nextBtn.addEventListener("click", () => {
    if (currentPage < Math.ceil(filteredPatients.length / patientsPerPage)) {
        currentPage++;
        renderPatients();
    }
});

const socket = io();

socket.on("new_alert", (data) => {
    const alertBox = document.getElementById("alert-box");
    const alertElement = document.getElementById("alert");
    const alertContent = document.getElementById("alert-content");
    const alertList = document.getElementById("alert-list");

    const timestamp = data.timestamp || new Date().toLocaleTimeString();
    const message = typeof data === "string" ? data : "⚠️ Alert received";
    
    // save alert in sessionStorage
    const storedAlerts = JSON.parse(sessionStorage.getItem("alerts") || "[]");
    storedAlerts.unshift({ timestamp, message });
    sessionStorage.setItem("alerts", JSON.stringify(storedAlerts.slice(0, 10)));

    const badge = document.getElementById("new-alert-badge");
    if (sessionStorage.getItem("newAlerts") === "true") {
        badge.classList.remove("hidden");
    }

    // dopo averli mostrati, rimuovi il flag
    sessionStorage.removeItem("newAlerts");

    // show pop-up
    if (alertBox && alertElement && alertContent) {
        alertBox.classList.remove("hidden");
        alertElement.textContent = `${timestamp} — ${message}`;
        alertContent.classList.remove("scale-95", "opacity-0");
        alertContent.classList.add("scale-100", "opacity-100");

        // automatically close pop-up after 10 seconds
        setTimeout(() => {
            alertBox.classList.add("hidden");
            alertContent.classList.remove("scale-100", "opacity-100");
            alertContent.classList.add("scale-95", "opacity-0");
        }, 10000);
    }

    // populate the alert-list
    if (alertList) {
        if (alertList.children.length === 1 && alertList.children[0].textContent.includes("No alerts")) {
            alertList.innerHTML = "";
        }

        const li = document.createElement("li");
        li.className = "whitespace-normal break-words leading-snug text-xs text-gray-800 w-full";
        li.title = `${timestamp} — ${message}`;
        li.textContent = `${timestamp} — ${message}`;

        if (alertList.children.length > 10) {
            alertList.removeChild(alertList.lastChild);
        }
    }
});

// manual pop-up closure
document.getElementById("close-alert-box").addEventListener("click", () => {
    document.getElementById("alert-box").classList.add("hidden");
});

// badge and alert list handler
document.addEventListener("DOMContentLoaded", () => {
    const badge = document.getElementById("new-alert-badge");
    const alertList = document.getElementById("alert-list");

    // badge
    if (badge && sessionStorage.getItem("newAlerts") === "true") {
        badge.classList.remove("hidden");
    }
    sessionStorage.removeItem("newAlerts");

    // alert list
    if (alertList) {
        const saved = JSON.parse(sessionStorage.getItem("alerts") || "[]");
        if (saved.length > 0) {
            alertList.innerHTML = "";
            saved.forEach(({ timestamp, message }) => {
                const li = document.createElement("li");
                li.className = "whitespace-normal break-words leading-snug text-xs text-gray-800 w-full";
                li.title = `${timestamp} — ${message}`;
                li.textContent = `${timestamp} — ${message}`;
                alertList.appendChild(li);
            });
        }
    }
});

applyFilters();