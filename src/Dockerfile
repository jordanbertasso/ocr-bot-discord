FROM python:3.8-alpine

WORKDIR /usr/src/bot

RUN apk add build-base zlib

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN mkdir sql

CMD [ "python", "-u", "main.py" ]
