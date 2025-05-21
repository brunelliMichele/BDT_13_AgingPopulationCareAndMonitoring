// ui.js

import { updateMapMarkers } from './map.js';
import { calculateAge } from './utils.js';

let patientsData = [];
let cityCoords = {};
let filteredPatients = [];
let currentPage = 1;
const patientsPerPage = 6;

// DOM refs
const container = document.getElementById("patientsContainer");
const searchInput = document.getElementById("searchInput");
const prevBtn = document.getElementById("prevPage");
const nextBtn = document.getElementById("nextPage");
const pageInfo = document.getElementById("pageInfo");

// event handling function
export function setupUIEvents() {
    searchInput.addEventListener("input", updateUI);
    document.getElementById("city-select").addEventListener("change", updateUI);

    prevBtn.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            renderPatients();
        }
    });

    nextBtn.addEventListener("click", () => {
        if (currentPage < Math.ceil(filteredPatients.length / patientsPerPage)) {
            currentPage++;
            renderPatients();
        }
    });
}

// function to update the graphical interface
export function updateUI() {
    if (patientsData.length === 0) {
        const jsonEl = document.getElementById("patientsJson");
        const coordsEl = document.getElementById("cityCoordsJson");
        patientsData = JSON.parse(jsonEl.textContent);
        cityCoords = JSON.parse(coordsEl.textContent);
    }

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
    updateMapMarkers(filteredPatients, selectedCity, cityCoords);
}

// patients rendering function
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