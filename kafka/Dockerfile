FROM python:3.10-slim

WORKDIR /BDT_13/kafka

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "db_to_kafka_stream.py"]