// Function to process earthquake data for visualizations
function processEarthquakeData(earthquakes) {
    // Magnitude distribution
    const magnitudeRanges = {
        '0-3': 0,
        '3-4': 0,
        '4-5': 0,
        '5-6': 0,
        '6+': 0
    };

    // Monthly frequency
    const monthlyData = {};
    
    // Regional distribution
    const regionalData = {};

    earthquakes.forEach(quake => {
        // Process magnitude distribution
        const magnitude = quake.magnitude;
        if (magnitude < 3) magnitudeRanges['0-3']++;
        else if (magnitude < 4) magnitudeRanges['3-4']++;
        else if (magnitude < 5) magnitudeRanges['4-5']++;
        else if (magnitude < 6) magnitudeRanges['5-6']++;
        else magnitudeRanges['6+']++;

        // Process monthly frequency
        const date = new Date(quake.date_ad);
        const monthYear = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        monthlyData[monthYear] = (monthlyData[monthYear] || 0) + 1;

        // Process regional distribution
        const region = quake.epicenter.split(',')[0].trim();
        regionalData[region] = (regionalData[region] || 0) + 1;
    });

    return { magnitudeRanges, monthlyData, regionalData };
}

// Function to create magnitude distribution chart
function createMagnitudeChart(data) {
    const ctx = document.getElementById('magnitudeChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(data.magnitudeRanges),
            datasets: [{
                label: 'Number of Earthquakes',
                data: Object.values(data.magnitudeRanges),
                backgroundColor: [
                    '#2ecc71',
                    '#f1c40f',
                    '#e67e22',
                    '#e74c3c',
                    '#c0392b'
                ],
                borderColor: '#fff',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Earthquake Magnitude Distribution'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Earthquakes'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Magnitude Range'
                    }
                }
            }
        }
    });
}

// Function to create monthly frequency chart
function createFrequencyChart(data) {
    const ctx = document.getElementById('frequencyChart').getContext('2d');
    const sortedMonths = Object.keys(data.monthlyData).sort();
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: sortedMonths,
            datasets: [{
                label: 'Earthquakes per Month',
                data: sortedMonths.map(month => data.monthlyData[month]),
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Monthly Earthquake Frequency'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Earthquakes'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Month'
                    }
                }
            }
        }
    });
}

// Function to create regional distribution chart
function createRegionalChart(data) {
    const ctx = document.getElementById('regionalChart').getContext('2d');
    const sortedRegions = Object.entries(data.regionalData)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10); // Show top 10 regions

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: sortedRegions.map(([region]) => region),
            datasets: [{
                data: sortedRegions.map(([, count]) => count),
                backgroundColor: [
                    '#e74c3c',
                    '#e67e22',
                    '#f1c40f',
                    '#2ecc71',
                    '#3498db',
                    '#9b59b6',
                    '#1abc9c',
                    '#d35400',
                    '#34495e',
                    '#16a085'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right'
                },
                title: {
                    display: true,
                    text: 'Top 10 Regions by Earthquake Frequency'
                }
            }
        }
    });
}

// Initialize visualizations when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Fetch earthquake data
    fetch('/get-earthquakes')
        .then(response => response.json())
        .then(earthquakes => {
            const processedData = processEarthquakeData(earthquakes);
            createMagnitudeChart(processedData);
            createFrequencyChart(processedData);
            createRegionalChart(processedData);
        })
        .catch(error => console.error('Error loading earthquake data:', error));
}); 