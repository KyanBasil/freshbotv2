// Make an AJAX request to fetch the schedule data from the server
fetch('schedule.json')
  .then(response => response.json())
  .then(data => {
    const scheduleContainer = document.getElementById('schedule');

    // Iterate over the schedule data and create HTML elements
    for (const time in data) {
      const timeSlot = document.createElement('div');
      timeSlot.classList.add('time-slot');

      const timeElement = document.createElement('div');
      timeElement.classList.add('time');
      timeElement.textContent = time;
      timeSlot.appendChild(timeElement);

      for (const zone in data[time]) {
        const zoneElement = document.createElement('div');
        zoneElement.classList.add('zone');
        zoneElement.textContent = `${zone}: ${data[time][zone]}`;
        timeSlot.appendChild(zoneElement);
      }

      scheduleContainer.appendChild(timeSlot);
    }
  })
  .catch(error => {
    console.error('Error fetching schedule data:', error);
  });
