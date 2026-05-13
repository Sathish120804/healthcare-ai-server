from flask import Flask, request, jsonify

app = Flask(__name__)

# ===================================
# STORE LATEST ACTION
# ===================================

latest_data = {
    "value": "NONE"
}

# ===================================
# UPDATE DATA FROM AI
# ===================================

@app.route('/update', methods=['POST'])
def update():

    global latest_data

    data = request.get_json()

    if data:

        latest_data = data

        print("Updated:", latest_data)

        return jsonify({
            "status": "success",
            "data": latest_data
        })

    return jsonify({
        "status": "failed"
    }), 400

# ===================================
# SEND DATA TO FLUTTER
# ===================================

@app.route('/data', methods=['GET'])
def data():

    return jsonify(latest_data)

# ===================================
# HOME
# ===================================

@app.route('/')
def home():

    return "Healthcare AI Server Running"

# ===================================
# RUN LOCAL SERVER
# ===================================

if __name__ == '__main__':

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
