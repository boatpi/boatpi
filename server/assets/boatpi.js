"use strict";

class BoatPi {
    constructor(webSocketUri, reconnectTimeout=5000) {
        this.authToken = null;
        this.connected = false;

        let connectWS = () => {
            this.websocket = new WebSocket(webSocketUri);

            this.websocket.onopen = () => {
                console.log('Server connected');
                document.dispatchEvent(new Event('boatpi.connected'));

                if (this.authToken) {
                    this.sendMessage({
                        action: 'authenticate',
                        token: this.authToken,
                    });
                }
            };

            this.websocket.onclose = () => {
                this.websocket = null;
                this.connected = false;

                // Try to reconnect
                let interval = setInterval(() => {
                    try {
                        connectWS();
                        clearInterval(interval);
                    } catch (error) {
                        console.error(error)
                    }
                }, reconnectTimeout);

                console.log(`Server disconnected, reconnection within ${reconnectTimeout / 1000} seconds`);
                document.dispatchEvent(new Event('boatpi.disconnected'));
            };

            this.websocket.onmessage = (message) => {
                try {
                    const data = JSON.parse(message.data);

                    if (!(message instanceof Object)) {
                        // If is not an Object, nothing to do, exit.
                        console.debug(message);
                        return;
                    }

                    if ('authentication' in data) {
                        if ('token' in data) {
                            this.authToken = data.token;
                            console.log('Authentication success');
                            document.dispatchEvent(new Event('boatpi.authentication.success'));
                        } else {
                            this.authToken = null;
                            console.log('Authentication failure');
                            document.dispatchEvent(new Event('boatpi.authentication.failure'));
                        }

                        return;
                    }

                    if ('boat' in data) {
                        if (data.boat instanceof Object) {
                            if (!this.connected) {
                                this.connected = true;
                                console.log('BoatPi connected');
                                document.dispatchEvent(new Event('boatpi.connected'));
                            }
                        } else {
                            this.connected = false;
                            console.log(`BoatPi disconnected, reconnection within ${reconnectTimeout / 1000} seconds`);
                            document.dispatchEvent(new Event('boatpi.disconnected'));
                        }
                    }

                    document.dispatchEvent(new CustomEvent('boatpi.update', {detail: data}));
                } catch (err) {
                    console.error(message.data)
                }
            };
        };

        connectWS();
    }

    isConnected(data) {
        return this.connected && this.websocket instanceof WebSocket && this.websocket.readyState === WebSocket.OPEN;
    }

    sendMessage(data) {
        if (!this.isConnected()) {
            return;
        }

        this.websocket.send(JSON.stringify(data));
    }

    captain(data) {
        if (!this.isConnected()) {
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