FROM alpine:3.20

RUN mkdir /config
RUN mkdir /server

COPY alexa.py /server/alexa.py
COPY server.py /server/server.py
COPY requirements.txt /server/requirements.txt

ENV ASL_CONFIG_PATH="/config/"
ENV CHROME_DRIVER="/usr/bin/chromedriver"

RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/community" > /etc/apk/repositories
RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories
RUN apk update

RUN apk add chromium
RUN apk add chromium-chromedriver
RUN apk add python3
RUN apk add py3-pip

RUN rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages -r /server/requirements.txt
RUN rm /server/requirements.txt

EXPOSE 4000 4000
ENTRYPOINT ["python3","/server/server.py"]
