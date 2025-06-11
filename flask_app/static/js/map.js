// map.js

// This module manages the interactive Leaflet map, including marker rendering for patients
// and real-time updates to risk levels via WebSocket.

import { calculateAge } from "./utils.js"; // load calculateAge function 

let map;
let currentMarkers = [];

export const socket = io();

// Initializes the Leaflet map and sets up a WebSocket listener for risk level updates.
export function initMap() {
    map = L.map("map-container").setView([42.4072, -71.3824], 8); // Massachusetts

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    // Fix mobile dimensions
    setTimeout(() => {
        map.invalidateSize();
    }, 300);

    // Listen for real-time updates and update patient markers accordingly
    socket.on("risk_level_update", (data) => {
        const updatedPatient = JSON.parse(data);
        // Find the patient in the current list and update his risk level
        const index = window.patients.findIndex(p => p.id === updatedPatient.id);
        if (index !== -1) {
            window.patients[index].risk_level = updatedPatient.risk_level;
            updateMapMarkers(window.patients);
        }
    });
}

// Clears existing markers and adds new ones based on patient data and optional city filter.
// Markers are color-coded based on the patient's risk level.
export function updateMapMarkers(patients, cityFilter = "", cityCoords = {}) {
    currentMarkers.forEach(marker => map.removeLayer(marker));
    currentMarkers = [];

    const filtered = patients.filter(p => !cityFilter || p.city.toLowerCase() === cityFilter.toLowerCase());

    filtered.forEach(p => {
        if (p.lat && p.lon) {
            // Choose marker color based on risk level
            const riskLevel = p.risk_level || 0;
            const iconColor = riskLevel > 60 ? 'red' : riskLevel > 30 ? 'orange' : 'green';
            const markerIcon = L.icon({
                iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-${iconColor}.png`,
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41]
            });

            // Create a custom popup with patient info
            const marker = L.marker([p.lat, p.lon], { icon: markerIcon })
                .addTo(map)
                .bindPopup(`
                    <div class="text-sm font-sans space-y-1" style="background-color: ${riskLevel > 60 ? '#f8d7da' : riskLevel > 30 ? '#fff3cd' : '#d4edda'}; padding: 8px; border-radius: 4px;">
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

    if (cityFilter && cityCoords[cityFilter]) {
        map.setView(cityCoords[cityFilter], 11);
    }
}