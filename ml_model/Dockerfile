FROM python:3.10-slim

RUN apt-get update && apt-get install -y build-essential libpq-dev postgresql-client

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY wait-for-postgres.sh /wait-for-postgres.sh
RUN chmod +x /wait-for-postgres.sh

COPY . .

RUN mkdir -p /app/output && useradd -ms /bin/bash appuser && chown -R appuser /app
RUN chmod -R u+w /app

USER root
RUN apt-get update && apt-get install -y cron


COPY cronjob /etc/cron.d/train_cron
RUN chmod 0644 /etc/cron.d/train_cron && crontab /etc/cron.d/train_cron

USER appuser
CMD ["/wait-for-postgres.sh", "db", "python", "train_model.py"]