FROM python:3.8-slim-buster

WORKDIR /usr/src/bot

RUN apt update && apt install -y tesseract-ocr libtesseract-dev libleptonica-dev pkg-config build-essential

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN mkdir sql

CMD [ "python", "-u", "main.py" ]
