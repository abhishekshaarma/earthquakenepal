// Initialize the map
const map = L.map('map').setView([27.7172, 85.3240], 7); // Centered on Nepal

// Add a tile layer (map background)
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Function to add earthquake markers to the map
function addEarthquakeMarkers(earthquakes) {
    const markers = [];
    earthquakes.forEach(quake => {
        // Check if latitude and longitude are valid numbers
        if (typeof quake.latitude === 'number' && typeof quake.longitude === 'number') {
            const marker = L.marker([quake.latitude, quake.longitude]).addTo(map);
            marker.bindPopup(`
                <strong>Epicenter:</strong> ${quake.epicenter}<br>
                <strong>Magnitude:</strong> ${quake.magnitude}
            `);
            markers.push(marker);
        } else {
            console.warn('Invalid coordinates for earthquake:', quake);
        }
    });

    // Fit map to all markers
    if (markers.length > 0) {
        const group = L.featureGroup(markers);
        map.fitBounds(group.getBounds());
    }
}
document.addEventListener('DOMContentLoaded', function() {
    // Initialize map if the map container exists
    const mapContainer = document.getElementById('map');
    if (mapContainer) {
      // Create map centered on Nepal
      const map = L.map('map').setView([28.3949, 84.1240], 7);
      
      // Add OpenStreetMap tile layer
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(map);
      
      // You would add earthquake markers here using data from your server
    }
    
    // Scroll to top button functionality
    const scrollUpButton = document.getElementById('scrollUp');
    if (scrollUpButton) {
      scrollUpButton.addEventListener('click', function(e) {
        e.preventDefault();
        window.scrollTo({
          top: 0,
          behavior: 'smooth'
        });
      });
    }
    
    
    // Earthquake Alert Popup functionality
    const earthquakeAlert = document.getElementById('earthquakeAlert');
    const closeAlertButton = document.getElementById('closeAlert');
    const viewDetailsButton = document.getElementById('viewAlertDetails');
    
    if (earthquakeAlert && closeAlertButton && viewDetailsButton) {
      // Function to show the alert popup
      function showEarthquakeAlert(data) {
        document.getElementById('alertLocation').textContent = data.location;
        document.getElementById('alertMagnitude').textContent = data.magnitude;
        document.getElementById('alertTime').textContent = data.time;
        earthquakeAlert.style.display = 'block';
      }
      
      // Close alert button functionality
      closeAlertButton.addEventListener('click', function() {
        earthquakeAlert.style.display = 'none';
      });
      
      // View details button functionality
      viewDetailsButton.addEventListener('click', function() {
        // Redirect to earthquake details page or scroll to the relevant section
        window.location.href = `/earthquake-details?id=${encodeURIComponent(currentEarthquakeId)}`;
        earthquakeAlert.style.display = 'none';
      });
      
      // For testing/demo purposes, show the alert after 5 seconds
      // In production, this would be triggered by a server event
      setTimeout(function() {
        showEarthquakeAlert({
          location: 'Dolakha, Nepal',
          magnitude: '4.5',
          time: 'February 25, 2025, 10:30 AM'
        });
      }, 5000);
      
      // Example of how to handle real-time updates
      // This would typically connect to a websocket or server-sent events
      /*
      const eventSource = new EventSource('/api/earthquake-events');
      
      eventSource.addEventListener('new-earthquake', function(e) {
        const data = JSON.parse(e.data);
        currentEarthquakeId = data.id;
        showEarthquakeAlert(data);
      });
      
      eventSource.onerror = function() {
        eventSource.close();
      };
      */
    }
  });
  
  // For demo purposes - global variable to store current earthquake ID
  let currentEarthquakeId = 'demo-earthquake-1';

// Fetch earthquake data from Flask and add markers
const loadingIndicator = document.getElementById('loading');

fetch('/get-earthquakes')
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        addEarthquakeMarkers(data);
    })
    .catch(error => {
        console.error('Error fetching earthquake data:', error);
    })
    .finally(() => {
        loadingIndicator.style.display = 'none'; // Hide loading indicator
    });

loadingIndicator.style.display = 'block'; // Show loading indicator

document.addEventListener('DOMContentLoaded', function() {
    // Initialize map if the map container exists
    const mapContainer = document.getElementById('map');
    if (mapContainer) {
      // Create map centered on Nepal
      const map = L.map('map').setView([28.3949, 84.1240], 7);
      
      // Add OpenStreetMap tile layer
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(map);
      
      // You would add earthquake markers here using data from your server
    }
    
    // Scroll to top button functionality
    const scrollUpButton = document.getElementById('scrollUp');
    if (scrollUpButton) {
      scrollUpButton.addEventListener('click', function(e) {
        e.preventDefault();
        window.scrollTo({
          top: 0,
          behavior: 'smooth'
        });
      });
    }
    
    // Earthquake Alert Popup functionality
    const earthquakeAlert = document.getElementById('earthquakeAlert');
    const closeAlertButton = document.getElementById('closeAlert');
    const viewDetailsButton = document.getElementById('viewAlertDetails');
    
    if (earthquakeAlert && closeAlertButton && viewDetailsButton) {
      // Function to show the alert popup
      function showEarthquakeAlert(data) {
        document.getElementById('alertLocation').textContent = data.location;
        document.getElementById('alertMagnitude').textContent = data.magnitude;
        document.getElementById('alertTime').textContent = data.time;
        earthquakeAlert.style.display = 'block';
      }
      
      // Close alert button functionality
      closeAlertButton.addEventListener('click', function() {
        earthquakeAlert.style.display = 'none';
      });
      
      // View details button functionality
      viewDetailsButton.addEventListener('click', function() {
        // Redirect to earthquake details page or scroll to the relevant section
        window.location.href = `/earthquake-details?id=${encodeURIComponent(currentEarthquakeId)}`;
        earthquakeAlert.style.display = 'none';
      });
      
      // For testing/demo purposes, show the alert after 5 seconds
      // In production, this would be triggered by a server event
      setTimeout(function() {
        showEarthquakeAlert({
          location: 'Dolakha, Nepal',
          magnitude: '4.5',
          time: 'February 25, 2025, 10:30 AM'
        });
      }, 5000);
      
      
    }
  });
  
