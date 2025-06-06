FROM python:3.10-slim

RUN apt-get update && apt-get install -y build-essential libpq-dev postgresql-client

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/output && useradd -ms /bin/bash appuser && chown -R appuser /app
RUN chmod -R u+w /app

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh


USER appuser
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "train_model.py"]