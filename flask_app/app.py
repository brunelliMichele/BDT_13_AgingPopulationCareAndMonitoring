# app.py
from flask import Flask
from flask_socketio import SocketIO
from routes import register_routes
from sockets import register_sockets
import eventlet
eventlet.monkey_patch()

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates")

socket_io = SocketIO(app, async_mode="eventlet")

register_routes(app)
register_sockets(socket_io)

if __name__ == "__main__":
    socket_io.run(app, host="0.0.0.0", port=8000)