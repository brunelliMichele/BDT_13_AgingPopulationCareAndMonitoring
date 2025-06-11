// ui.js

// This script manages the user interface for listing patients,
// including search, pagination, and integration with the map.

import { updateMapMarkers } from './map.js';
import { calculateAge } from './utils.js';

// Global variables for patient data and pagination
let patientsData = [];
let cityCoords = {};
let filteredPatients = [];
let currentPage = 1;
const patientsPerPage = 6;

// References to DOM elements used in the UI
const container = document.getElementById("patientsContainer");
const searchInput = document.getElementById("searchInput");
const prevBtn = document.getElementById("prevPage");
const nextBtn = document.getElementById("nextPage");
const pageInfo = document.getElementById("pageInfo");

// Initializes UI event listeners for search input, city filter, and pagination controls
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

// Updates the UI with filtered patient data and refreshes the map markers
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

// Renders the list of patients on the current page, showing key info and risk levels
function renderPatients() {
    container.innerHTML = "";
    const start = (currentPage - 1) * patientsPerPage;
    const end = start + patientsPerPage;
    const patientsToShow = filteredPatients.slice(start, end);

    patientsToShow.forEach(p => {
        const div = document.createElement("div");
        div.className = "bg-teal-50 border border-teal-200 p-4 rounded-lg shadow-md";

        // Display risk level with color based on severity, or a placeholder if missing
        let riskLevelDisplay = '';
        if (p.risk_level !== undefined && p.risk_level !== null) {
            let riskColor = 'text-green-600';
            if (p.risk_level > 60) {
                riskColor = 'text-red-600';
            } else if (p.risk_level > 30) {
                riskColor = 'text-yellow-600';
            }
            riskLevelDisplay = `<p class="text-sm font-semibold ${riskColor}">Risk Level: ${p.risk_level.toFixed(1)}%</p>`;
        } else {
            riskLevelDisplay = `<p class="text-sm text-gray-500 italic">Risk level not available</p>`;
        }

        div.innerHTML = `
            <h3 class="text-lg font-bold text-teal-700">🧓 ${p.name} ${p.middlename ? p.middlename + ' ' : ''}${p.surname}</h3>
            <p class="text-gray-700 text-sm"><strong>ID:</strong> ${p.id}</p>
            <p class="text-gray-700 text-sm"><strong>Age:</strong> ${calculateAge(p.birthdate)} years</p>
            <p class="text-gray-700 text-sm"><strong>City:</strong> ${p.city}</p>
            ${riskLevelDisplay}
            <a href="${p.url}" class="text-teal-600 hover:text-teal-800 underline text-sm">View details</a>
        `;
        container.appendChild(div);
    });

    pageInfo.textContent = `Page ${currentPage} of ${Math.ceil(filteredPatients.length / patientsPerPage)}`;
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage >= Math.ceil(filteredPatients.length / patientsPerPage);
}