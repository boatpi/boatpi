$(() => {
    "use strict";
    const webSocketProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const webSocketUri = webSocketProtocol + '//' + location.hostname + ':' + location.port + '/ws';

    const loader = $("#loader");
    const cockpit = $("#cockpit");
    const power = $("#power");
    const wheel = $("#wheel");
    const passengers = $("#passengers");
    const crew = $("#crew");

    const initialPosition = [41.9027835, 12.496365500000024];
    const map = L.map('mapid').setView(initialPosition, 16);
    const marker = L.marker(initialPosition).addTo(map);

    L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
        maxZoom: 18,
        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, ' +
        '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
        'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
        id: 'mapbox.streets'
    }).addTo(map);

    document.addEventListener('boatpi.connected', function (e) {
        loader.hide();
        cockpit.show();
    });

    document.addEventListener('boatpi.disconnected', function (e) {
        loader.show();
        cockpit.hide();
    });

    document.addEventListener('boatpi.update', function (e) {
        passengers.text(e.detail.passengers);
        crew.text(e.detail.crew);

        if ('boat' in e.detail && e.detail.boat instanceof Object) {
            let boat = e.detail.boat;

            if ('wheel' in boat) {
                wheel.slider('setValue', Number(boat.wheel));
            }

            if ('power' in boat) {
                power.slider('setValue', Number(boat.power));
            }

            if ('gps_position' in boat) {
                let position = [boat.gps_position.latitude, boat.gps_position.longitude];
                marker.setLatLng(position);
                map.setView(position);
            }
        }
    });

    const boatpi = new BoatPi(webSocketUri);
    let timestamp = 0;

    wheel.slider({
        min: -50,
        max: 50,
        value: 0,
        precision: 2,
        ticks: [-50, 0, 50],
        ticks_positions: [0, 50, 100],
        ticks_labels: ['Left', 'Center', 'Rigth'],
    });

    wheel.on("slideStop", function (slideEvt) {
        boatpi.captain({wheel: Number(slideEvt.value)});
        timestamp = Date.now() / 1000;
    });

    power.slider({
        min: -20,
        max: 100,
        value: 0,
        precision: 2,
        reversed: true,
        orientation: 'vertical',
        // ticks: [-20, 0, 100],
        // ticks_positions: [100, 15, 0],
        // ticks_labels: ['R', 0, 100],
    });

    power.on("slideStop", function (slideEvt) {
        boatpi.captain({power: Number(slideEvt.value)});
        timestamp = Date.now() / 1000;
    });

    // TODO: Implement authentication and remove this shit
    setTimeout(() => {
        boatpi.authenticate('Tizio', 'Qualunque');
    }, 1000);
});