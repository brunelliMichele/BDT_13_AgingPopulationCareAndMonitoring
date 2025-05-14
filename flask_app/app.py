from flask import Flask, jsonify

# create flask app
app = Flask(__name__)

# populate flask app
@app.route("/")
def index():
    return jsonify({"msg": "Flask is running!"})

# run flask app on localhost:5000
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)