from flask import Flask, request, jsonify

app = Flask(__name__)

# Store latest action
latest_data = {
    "value": "NONE"
}

# -----------------------------------
# UPDATE DATA FROM AI
# -----------------------------------

@app.route('/update', methods=['POST'])
def update():

    global latest_data

    latest_data = request.json

    print("Updated:", latest_data)

    return jsonify({
        "status": "success"
    })

# -----------------------------------
# SEND DATA TO FLUTTER
# -----------------------------------

@app.route('/data')
def data():

    return jsonify(latest_data)

# -----------------------------------
# HOME
# -----------------------------------

@app.route('/')
def home():

    return "Healthcare AI Server Running"

# -----------------------------------
# RUN SERVER
# -----------------------------------

if __name__ == '__main__':

    app.run(
        host='0.0.0.0',
        port=5000
    )