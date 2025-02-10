from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# URL Binance API
BINANCE_API_URL = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"

@app.route('/price', methods=['GET'])
def get_price():
    """Получает цену BTC/USDT с Binance"""
    try:
        response = requests.get(BINANCE_API_URL)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
