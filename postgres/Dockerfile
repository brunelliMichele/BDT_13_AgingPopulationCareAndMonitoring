FROM python:3.10-slim

RUN apt-get update && apt-get install -y default-jre wget unzip

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

RUN wget https://github.com/synthetichealth/synthea/releases/latest/download/synthea-with-dependencies.zip && \
    unzip synthea-with-dependencies.zip && \
    rm synthea-with-dependencies.zip

COPY synthea_loader.py .

CMD ["python", "synthea_loader.py"]