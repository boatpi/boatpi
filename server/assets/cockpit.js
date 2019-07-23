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

    /* modem */
    const modem = $("#modem");
    const sinr = $("#sinr");
    const rsrp = $("#rsrp");
    const rsrq = $("#rsrq");

    const cpu = $("#cpu");
    const ram = $("#ram");
    const batt = $("#batt");

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

            if ('gps' in boat && boat.gps instanceof Object) {
                let position = [boat.gps.latitude, boat.gps.longitude];
                marker.setLatLng(position);
                map.setView(position);
            }

            if ('cpu_load' in boat) {
                cpu.find('.progress-bar').text(boat.cpu_load + '%').width(boat.cpu_load + '%');
            }

            if ('memory' in boat && boat.memory instanceof Object) {
                ram.find('.progress-bar').text(boat.memory.percentage + '%').width(boat.memory.percentage + '%');
            }

            if ('battery' in boat && boat.modem instanceof Object) {
                // TODO: Show battery load and charge status
            }

            if ('modem' in boat && boat.modem instanceof Object) {
                if (boat.modem.sinr) {
                    sinr.find('.progress-bar').text(boat.modem.sinr + '%').width(boat.modem.sinr + '%');
                } else {
                    sinr.find('.progress-bar').text('None').width(0);
                }

                if (boat.modem.rsrp) {
                    rsrp.find('.progress-bar').text(boat.modem.rsrp + '%').width(boat.modem.rsrp + '%');
                } else {
                    rsrp.find('.progress-bar').text('None').width(0);
                }

                if (boat.modem.rsrq) {
                    rsrq.find('.progress-bar').text(boat.modem.rsrq + '%').width(boat.modem.rsrq + '%');
                } else {
                    rsrq.find('.progress-bar').text('None').width(0);
                }
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