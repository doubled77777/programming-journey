from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return "Sales System funcionando"


@app.route("/process_order", methods=["POST"])
def process_order():
    data = request.json

    print("Datos recibidos:")
    print(data)

    return jsonify({
        "status": "received",
        "message": "Datos recibidos correctamente"
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)