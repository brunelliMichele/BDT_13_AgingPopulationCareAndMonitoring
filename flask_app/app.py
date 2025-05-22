# app.py
from flask import Flask
from flask_socketio import SocketIO
from routes import register_routes

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates")

socket_io = SocketIO(app, async_mode="threading", cors_allowed_origins="*")

register_routes(app)

if __name__ == "__main__":
    from sockets import register_sockets
    register_sockets(socket_io)
    socket_io.run(app, host="0.0.0.0", port=8000, allow_unsafe_werkzeug=True)