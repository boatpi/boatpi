$(() => {
    "use strict";

    const webSocketProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const webSocketUri = webSocketProtocol + '//' + location.hostname + ':' + location.port + '/ws';

    const boatpi = new BoatPi(webSocketUri);

    const map = L.map('mapid').setView([41.9027835, 12.496365500000024], 16);
    const marker = L.marker([41.9027835, 12.496365500000024]).addTo(map);

    L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
        maxZoom: 18,
        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, ' +
        '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
        'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
        id: 'mapbox.streets'
    }).addTo(map);

    setTimeout(() => {
        boatpi.authenticate('Tizio', 'Qualunque');
    }, 1000);

    setTimeout(() => {
        boatpi.captain({power:.01, wheel:2})
    }, 2000);

    document.addEventListener('boatpi.update', function (e) {
        if (e.detail.gps_position) {
            let position = [e.detail.gps_position.latitude, e.detail.gps_position.longitude];
            marker.setLatLng(position);
            map.setView(position);
        }
    });
});
