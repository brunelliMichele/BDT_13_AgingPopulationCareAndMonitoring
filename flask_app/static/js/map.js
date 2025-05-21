// map.js

import { calculateAge } from "./utils.js";

let map;
let currentMarkers = [];

// function for initializing the map
export function initMap() {
    map = L.map("map-container").setView([42.4072, -71.3824], 8); // Massachusetts

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    // Fixa le dimensioni su mobile
    setTimeout(() => {
        map.invalidateSize();
    }, 300);
}

// map marker update function
export function updateMapMarkers(patients, cityFilter = "", cityCoords = {}) {
    currentMarkers.forEach(marker => map.removeLayer(marker));
    currentMarkers = [];

    const filtered = patients.filter(p => !cityFilter || p.city.toLowerCase() === cityFilter.toLowerCase());

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

    if (cityFilter && cityCoords[cityFilter]) {
        map.setView(cityCoords[cityFilter], 11);
    }
}