FROM python:3.8-slim-buster

COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install gunicorn
ENV GUNICORN_BIN /usr/local/bin/gunicorn

WORKDIR /app

COPY *.py ./
COPY app ./app
COPY letter_analytics ./letter_analytics

RUN chgrp -R 0 /app \
 && chmod -R g+rwX /app

ENV GUNICORN_WORKER_AMOUNT 4
ENV GUNICORN_TIMEOUT 300
ENV GUNICORN_RELOAD ""

ENV MPLCONFIGDIR=/app/.config/matplotlib

EXPOSE 5000

USER 9008

COPY run /run.sh

ENTRYPOINT [ "/run.sh" ]