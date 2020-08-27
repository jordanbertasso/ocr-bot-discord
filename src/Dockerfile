FROM python:3.8

WORKDIR /usr/src/bot

RUN apt-get install -y git

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN pip install -U git+https://github.com/Rapptz/discord-ext-menus

COPY ./src .

RUN mkdir sql

CMD [ "python", "-u", "main.py" ]
