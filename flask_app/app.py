from flask import Flask, render_template
from flask_socketio import SocketIO
from confluent_kafka import Consumer
import threading
import json

# create flask app and initialize webSocket
app = Flask(__name__)
socket_io = SocketIO(app)

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
        print(f"[KAFKA] - {data}") # just for debugging
        socket_io.emit("kafka_message", {"data": data})
    
    consumer.close()

# set primary route
@app.route("/")
def index():
    return render_template("index.html")

@app.route('/test')
def test_emit():
    socket_io.emit('kafka_message', {'data': '{"test": "OK"}'})
    return "Sent"

# run flask app and kafka consumer on localhost:5000
if __name__ == "__main__":
    threading.Thread(target = consume_kafka, daemon = True).start()
    socket_io.run(app, host="0.0.0.0", port=8000, debug=True) # debug=True just for develop