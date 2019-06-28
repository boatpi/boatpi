BoatPi
======
An analog Boat into a Digital Ocean

> This is a work in progres project, we are working hard to sail soon.
>> SO STAY TUNED!

## For developers and local testing
### With Docker
Create your own `docker-compose.override.yml` file with ports mapping as you like

Run `docker-compose up -d` to start up,
keep an eye on the logs `docker-compose logs -f`

### Without Docker
Open two terminal sessions, then run
```
pip3 install -r boat/requirments.txt
python3 boat/boat.py
```
and
```
pip3 install -r server/requirments.txt
python3 server/server.py
```

### Ready
Now you can browse to `http://localhost/`
