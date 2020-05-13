FROM python:3.8

WORKDIR /usr/src/bot

RUN apt-get install -y git

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN mkdir sql

RUN pip install -U git+https://github.com/Rapptz/discord-ext-menus

CMD [ "python", "-u", "main.py" ]
