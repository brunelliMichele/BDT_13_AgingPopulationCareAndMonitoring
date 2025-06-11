# app.py

# This is the main entry point of the Flask application.
# It initializes the Flask app, sets up Socket.IO for real-time communication,
# and registers all routes and socket events.

from flask import Flask
from flask_socketio import SocketIO
from routes import register_routes

# Initialize the Flask app with static and template directories
app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates")

# Create a Socket.IO instance with threading support and CORS enabled
socket_io = SocketIO(app, async_mode="threading", cors_allowed_origins="*")

# Register HTTP routes defined in the routes module
register_routes(app)

if __name__ == "__main__":
    # Register and run the Socket.IO server when this script is executed directly
    from sockets import register_sockets
    register_sockets(socket_io)
    socket_io.run(app, host="0.0.0.0", port=8000, allow_unsafe_werkzeug=True)