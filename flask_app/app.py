from flask import Flask, render_template
from flask_socketio import SocketIO
from confluent_kafka import Consumer
import time

# create flask app and initialize webSocket
app = Flask(
    __name__,
    static_folder = "static",
    template_folder = "templates"
    )
socket_io = SocketIO(app, cors_allowed_origins = "*")

# Kafka Config
kafka_config = {
    "bootstrap.servers": "kafka:9092", # kafka container name
    "group.id": "flask-consumer-group", # consumer group name
    "auto.offset.reset": "earliest", # with no offset, start from the beginning
    "group.id": "smart_home" # group.id name
}

# Kafka consumer with error handling
def consume_kafka():
    time.sleep(10)
    consumer = Consumer(kafka_config)
    print(f"Started kafka consumer") # log
    consumer.subscribe(["smart_home_data"])
    print(f"Kafka subsribed on topic 'smart_home_data'") #log

    while True:
        msg = consumer.poll(1.0)
        print(f"Polling...") # log
        if msg is None:
            print(f"No message recived") # log
            continue
        if msg.error():
            print(f"[KAFKA] - Error: {msg.error()}") # log
            continue
        data = msg.value().decode("utf-8")
        print(f"[KAFKA] - {data}") # log
        print(f"[MESSAGE DIMENSION] - {len(data)} bytes") # log

        print(f"📤 Emitting to socket: {data[:80]}...")  # log
        socket_io.emit('kafka_message', {'data': data})
        # socket_io.emit('kafka_message', {'data': "test"})
        print(f"[SocketIO] - Emit: {data}") # log
    
    consumer.close()

# set primary route
@app.route("/")
def index():
    return render_template("index.html")

# run flask app and kafka consumer on localhost:8000
if __name__ == "__main__":
    socket_io.start_background_task(consume_kafka)
    socket_io.run(app, host="0.0.0.0", port=8000)