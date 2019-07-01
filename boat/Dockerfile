FROM python:3.7-alpine3.9

RUN apk add --update --no-cache \
    build-base \
    linux-headers

COPY requirments.txt /srv/

WORKDIR /srv

RUN pip install -r requirments.txt

CMD ./boat.py
EXPOSE 8000
ENV APP_PORT=8000
