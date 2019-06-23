$(() => {
    "use strict";

    const webSocketProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const webSocketUri = webSocketProtocol + '//' + location.hostname + ':' + location.port + '/ws';

    const boatpi = new BoatPi(webSocketUri);


    setTimeout(() => {
        boatpi.authenticate('Tizio', 'Qualunque');
    }, 1000);
});
