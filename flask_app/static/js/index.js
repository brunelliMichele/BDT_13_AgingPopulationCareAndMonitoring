// !!-- VARIABLES SECTION --!!
const patientsData = JSON.parse(document.getElementById("patientsJson").textContent);
const cityCoords = JSON.parse(document.getElementById("cityCoordsJson").textContent);
const patientsPerPage = 6;
let currentPage = 1;
let filteredPatients = [...patientsData];

const container = document.getElementById("patientsContainer");
const searchInput = document.getElementById("searchInput");
const prevBtn = document.getElementById("prevPage");
const nextBtn = document.getElementById("nextPage");
const pageInfo = document.getElementById("pageInfo");

// default map
const map = L.map("map-container").setView([42.4072, -71.3824], 8);  // Massachusetts

// Tile layer base
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);
let currentMarkers = [];


// !!-- FUNCTIONS SECTION --!!
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
            <p class="text-gray-700 text-sm"><strong>Age:</strong> ${calculateAge(p.birthdate)} years</p>
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

// function for update the map markers
function updateMapMarkers(cityFilter = "") {
    // Remove all markers
    currentMarkers.forEach(marker => map.removeLayer(marker));
    currentMarkers = [];

    const filtered = patientsData.filter(p => !cityFilter || p.city === cityFilter);

    filtered.forEach(p => {
        if (p.lat && p.lon) {
            const marker = L.marker([p.lat, p.lon])
                .addTo(map)
                .bindPopup(`
                <div class="text-sm font-sans space-y-1">
                    <div class="font-semibold text-teal-700">🧓 ${p.name} ${p.surname}</div>
                    <div class="text-gray-600">📍 ${p.city}</div>
                    <div class="text-gray-600">🎂 Age: ${calculateAge(p.birthdate)}</div>
                    <a href="${p.url}" style="color: black;" class="inline-block mt-2 px-3 py-1 bg-teal-600 text-black text-xs font-semibold rounded hover:bg-teal-700 transition no-underline">
                        ➡ View patient details
                    </a>
                </div>
            `);
            currentMarkers.push(marker);
        }
    });

    // recenter the map
    if (cityFilter && cityCoords[cityFilter]) {
        map.setView(cityCoords[cityFilter], 11);
    }
}

// function for calculate the age
function calculateAge(birthdateStr){
    if(!birthdateStr) return "N/A";
    const birthdate = new Date(birthdateStr);
    const today = new Date();
    let age = today.getFullYear() - birthdate.getFullYear();
    const m = today.getMonth() - birthdate.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birthdate.getDate())){
        age--;
    }
    return age;
}

/* // for handle test alert 
function triggerTestAlert() {
    socket.emit("test_alert", {
        message: "🔥 Test alert triggered manually",
        timestamp: new Date().toLocaleTimeString()
    });
} */

// !!-- EVENTS SECTION --!!
// event handler for searchbox
searchInput.addEventListener("input", applyFilters);
document.getElementById("city-select").addEventListener("change", () => {
    applyFilters();
    const selectedCity = document.getElementById("city-select").value;
    updateMapMarkers(selectedCity);
});

// badge and alert list handler
document.addEventListener("DOMContentLoaded", () => {
    const badge = document.getElementById("new-alert-badge");
    const alertList = document.getElementById("alert-list");

    // badge
    if (badge) {
    const count = parseInt(sessionStorage.getItem("newAlertsCount") || "0");
    if (count > 0) {
        badge.textContent = count;
        badge.classList.remove("hidden");
    }
}

    // alert list
    if (alertList) {
        const saved = JSON.parse(sessionStorage.getItem("alerts") || "[]");
        if (saved.length > 0) {
            alertList.innerHTML = "";
            const newCount = parseInt(sessionStorage.getItem("newAlertsCount") || "0");
            let count = 0;

            saved.forEach(({ timestamp, message, isNew }) => {
                const li = document.createElement("li");
                li.className = "bg-rose-100 text-rose-700 border border-rose-200 px-2 py-1 rounded text-xs leading-tight break-words";
                li.title = `${timestamp} — ${message}`;
                li.textContent = `${timestamp} — ${message}`;

                if (isNew && count < newCount) {
                    li.dataset.new = "true";
                    count++;
                }

                alertList.appendChild(li);
            });
        }
    }
});

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


// !!-- WEB SOCKET SECTION --!!
const socket = io();

socket.on("new_alert_message", (data) => {
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
    const newCount = parseInt(sessionStorage.getItem("newAlertsCount") || "0");

    if (badge && newCount > 0) {
        badge.textContent = newCount;
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
        li.className = "bg-rose-100 text-rose-700 border border-rose-200 px-2 py-1 rounded text-xs leading-tight break-words";
        li.title = `${timestamp} — ${message}`;
        li.textContent = `${timestamp} — ${message}`;
        li.dataset.new = "true";

        alertList.insertBefore(li, alertList.firstChild);

        if (alertList.children.length > 10) {
            alertList.removeChild(alertList.lastChild);
        }
    }
});

// listener for click on "pop-up closure"
document.getElementById("close-alert-box").addEventListener("click", () => {
    document.getElementById("alert-box").classList.add("hidden");
});

// listener for click on "new alert badge"
document.getElementById("new-alert-badge").addEventListener("click", () => {
    const newItems = document.querySelectorAll("#alert-list li[data-new='true']");
    newItems.forEach(el => {
        el.classList.add("bg-yellow-200", "border-2", "border-yellow-500");
        setTimeout(() => {
            el.classList.remove("bg-yellow-200", "border-2", "border-yellow-500");
        }, 3000);
        el.removeAttribute("data-new");
    });

    if (newItems.length > 0) {
        newItems[0].scrollIntoView({ behavior: "smooth", block: "center" });
    }

    const badge = document.getElementById("new-alert-badge");
    badge.textContent = "0";
    badge.classList.add("hidden");

    sessionStorage.setItem("newAlertsCount", "0");
    sessionStorage.removeItem("newAlerts");

    const saved = JSON.parse(sessionStorage.getItem("alerts") || "[]");
    const cleared = saved.map(alert => ({ ...alert, isNew: false }));
    sessionStorage.setItem("alerts", JSON.stringify(cleared));
});



applyFilters();
updateMapMarkers();

