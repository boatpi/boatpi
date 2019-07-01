"use strict";

class BoatPi {
    constructor(webSocketUri, reconnectTimeout=5000) {
        this.authToken = null;

        let connectWS = () => {
            this.websocket = new WebSocket(webSocketUri);

            this.websocket.onopen = () => {
                console.log('BoatPi connected');
                dispatchEvent(new Event('boatpi.connected'));

                if (this.authToken) {
                    this.sendMessage({
                        action: 'authenticate',
                        token: this.authToken,
                    });
                }
            };

            this.websocket.onclose = () => {
                this.websocket = null;

                // Try to reconnect
                let interval = setInterval(() => {
                    try {
                        connectWS();
                        clearInterval(interval);
                    } catch (error) {
                        console.error(error)
                    }
                }, reconnectTimeout);

                console.log(`BoatPi disconnected, reconnection within ${reconnectTimeout / 1000} seconds`);
                dispatchEvent(new Event('boatpi.disconnected'));
            };

            this.websocket.onmessage = (message) => {
                try {
                    const data = JSON.parse(message.data);

                    if (data.event === 'authentication') {
                        if (data.status === 'success') {
                            this.authToken = data.token;
                            console.log('Authentication success');
                            dispatchEvent(new Event('boatpi.authentication.success'));
                        } else {
                            this.authToken = null;
                            dispatchEvent(new Event('boatpi.authentication.failure'));
                        }
                    } else {
                        console.warn(data);
                    }
                } catch (err) {
                    console.error(message.data)
                }
            };
        };

        connectWS();
    }

    sendMessage(data) {
        if (!this.websocket instanceof WebSocket || this.websocket.readyState !== WebSocket.OPEN) {
            return;
        }

        this.websocket.send(JSON.stringify(data));
    }

    captain(data) {
        if (!this.websocket instanceof WebSocket || this.websocket.readyState !== WebSocket.OPEN) {
            return;
        }

        if (!this.authToken) {
            console.error('You are not authenticated, only Captains can put commands to the boat.');
            return;
        }

        data.action = 'captain';

        this.websocket.send(JSON.stringify(data));
    }

    authenticate(username, password) {
        this.sendMessage({
            action: 'authenticate',
            username: username,
            password: password,
        });
    }
}