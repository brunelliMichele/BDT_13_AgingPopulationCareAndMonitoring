from flask import Flask, render_template
from flask_socketio import SocketIO
from confluent_kafka import Consumer
import threading
import json

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
    "group.id": "smart_home"
}

# Kafka consumer with error handling
def consume_kafka():
    consumer = Consumer(kafka_config)
    consumer.subscribe(["smart_home_data"])

    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"[KAFKA] - Error: {msg.error()}")
            continue
        data = msg.value().decode("utf-8")
        print(f"[KAFKA] - {data}") # debugging
        socket_io.emit("kafka_message", {"data": data})
        print(f"[SocketIO] - Emit: {data}") # debugging
    
    consumer.close()

# set primary route
@app.route("/")
def index():
    return render_template("index.html")

@app.route('/test_emit')
def test_emit():
    socket_io.emit('kafka_message', {'data': '{"test": "OK"}'})
    return "Message Sent"

# run flask app and kafka consumer on localhost:5000
if __name__ == "__main__":
    socket_io.start_background_task(consume_kafka)
    socket_io.run(app, host="0.0.0.0", port=8000, debug=True) # debug=True just for debugging