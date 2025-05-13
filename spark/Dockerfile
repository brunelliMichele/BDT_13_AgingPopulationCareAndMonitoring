FROM bitnami/spark:latest

COPY . /spark
WORKDIR /spark

RUN pip install --no-cache-dir -r requirements.txt

CMD ["spark-submit", "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0", "spark_stream.py"]