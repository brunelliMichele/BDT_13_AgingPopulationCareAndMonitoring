from flask import Flask, render_template

# create flask app
app = Flask(__name__)

# populate flask app
@app.route("/")
def index():
    return render_template("index.html")

# run flask app on localhost:5000
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True) # debug=True just for develop