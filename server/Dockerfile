FROM python:3.7-alpine3.9

RUN apk add --update --no-cache \
    build-base

COPY requirments.txt /srv/

WORKDIR /srv

RUN pip install -r requirments.txt

CMD ./server.py
EXPOSE 8000
