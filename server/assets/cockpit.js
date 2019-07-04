 $(() => {
        "use strict";
        const webSocketProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        const webSocketUri = webSocketProtocol + '//' + location.hostname + ':' + location.port + '/ws';

        const boatpi = new BoatPi(webSocketUri);

        let timestamp = 0;

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
        // With JQuery
        let timone = $("#timone").slider({
            min: -5,
            max: 5,
            tooltip: 'always'
        });

        let acceleratore = $("#acceleratore").slider({
            min: -20,
            max: 100,
            reversed: true,
            orientation: 'vertical',
            tooltip_position: 'left',
            tooltip: 'always'
        });

        document.addEventListener('boatpi.update', function (e) {

            if('wheel' in e.detail){
                 timone.slider('setValue', Number(e.detail.wheel));
            }
             if('power' in e.detail){
                 acceleratore.slider('setValue', Number(e.detail.power));
             }

            if ('gps_position' in e.detail) {
                let position = [e.detail.gps_position.latitude, e.detail.gps_position.longitude];
                console.log(position)
                marker.setLatLng(position);
                map.setView(position);
            }
        });

        $("#acceleratore").on("slideStop", function (slideEvt) {
            boatpi.captain({power: Number(slideEvt.value)});
            timestamp = Date.now()/1000;
        });

        $("#timone").on("slideStop", function (slideEvt) {
            boatpi.captain({wheel: Number(slideEvt.value)});
            timestamp = Date.now()/1000;
        });
    });