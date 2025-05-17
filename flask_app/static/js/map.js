// Initialize the map
var map = L.map('map').setView([51.505, -0.09], 13);

// Add the tile layer
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

// Create a variable to store city data and current marker
let cityData = {};
let currentMarker = null;

// Fetch city data from API endpoint
fetch('/api/city-data')
    .then(response => response.json())
    .then(data => {
        cityData = data;
        console.log("City data loaded:", cityData);
        
        // Now set up the event listener once we have the data
        document.getElementById('city-select').addEventListener('change', function() {
            const selectedCity = this.value;
            console.log("Selected city:", selectedCity);
            
            if (selectedCity && cityData[selectedCity]) {
                // Remove previous marker if exists
                if (currentMarker) {
                    map.removeLayer(currentMarker);
                }
                
                // Focus map on selected city with zoom level 13
                map.setView(cityData[selectedCity], 13);
                
                // Add a marker for the selected city
                currentMarker = L.marker(cityData[selectedCity])
                    .addTo(map)
                    .bindPopup(selectedCity)
                    .openPopup();
            }
        });
    })
    .catch(error => console.error("Error loading city data:", error));