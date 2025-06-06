FROM python:3.10-slim

RUN apt-get update && apt-get install -y default-jre curl

WORKDIR /app

COPY synthea-with-dependencies.jar /app/

COPY . .

RUN printf 'exporter.fhir.export = false\n\
exporter.csv.export = true\n\
exporter.baseDirectory = output\n\
exporter.csv.folder = csv\n' > /app/custom.properties

RUN apt-get update && apt-get install -y python3 python3-pip && \
    pip install --no-cache-dir -r requirements.txt