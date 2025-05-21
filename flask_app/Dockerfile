# Dockerfile

FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

# Installa dipendenze (usa --no-cache-dir per alleggerire)
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Espone la porta (modifica se usi un'altra)
EXPOSE 8000

# Avvia il server Flask+SocketIO con eventlet
CMD ["python", "app.py"]