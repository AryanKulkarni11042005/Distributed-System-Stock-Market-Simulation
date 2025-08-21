from flask import Flask, jsonify, request
from flask_cors import CORS
import Pyro4
import threading
import random
import time
import sys
import os
from datetime import datetime
from bson import json_util
import json

# Add path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.config import load_config
from utils.logger import setup_logger, log_with_sync_time
# Import the MongoDB collections from the updated connection script
from database.connection import init_db, stocks_collection
from utils.exceptions import StockNotFoundException

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
        "supports_credentials": True
    }
})
app.config.from_object(load_config())

logger = setup_logger(__name__)

# Initialize database (this will run init_sample_data if needed)
init_db()

def mongo_to_dict(obj):
    """
    Helper function to convert MongoDB documents (including ObjectId) to a JSON-serializable dictionary.
    """
    return json.loads(json_util.dumps(obj))

@Pyro4.expose
class StockExchangeRPC:
    """Pyro4 RPC interface for Stock Exchange Service, now using MongoDB."""

    def get_stock_price(self, symbol):
        """Get current stock price via RPC from MongoDB."""
        try:
            stock = stocks_collection.find_one({'symbol': symbol})
            if not stock:
                raise StockNotFoundException(f"Stock {symbol} not found")
            return stock['current_price']
        except Exception as e:
            logger.error(f"RPC Error getting stock price for {symbol}: {e}")
            raise

    def get_all_stocks(self):
        """Get all stocks via RPC from MongoDB."""
        try:
            stocks = list(stocks_collection.find({}))
            return mongo_to_dict(stocks)
        except Exception as e:
            logger.error(f"RPC Error getting all stocks: {e}")
            raise

    def get_stock(self, symbol):
        """Get stock details via RPC from MongoDB."""
        try:
            stock = stocks_collection.find_one({'symbol': symbol})
            if not stock:
                raise StockNotFoundException(f"Stock {symbol} not found")
            return mongo_to_dict(stock)
        except Exception as e:
            logger.error(f"RPC Error getting stock {symbol}: {e}")
            raise

    def update_stock_price(self, symbol, new_price):
        """Update stock price via RPC in MongoDB."""
        try:
            stock = stocks_collection.find_one({'symbol': symbol})
            if not stock:
                raise StockNotFoundException(f"Stock {symbol} not found")

            old_price = stock['current_price']
            result = stocks_collection.update_one(
                {'symbol': symbol},
                {'$set': {'current_price': new_price, 'last_updated': datetime.utcnow()}}
            )

            if result.modified_count == 0:
                raise Exception("Failed to update stock price.")

            log_with_sync_time(logger, 20, f"Updated {symbol} price from {old_price} to {new_price}", 'stock_exchange')
            return self.get_stock(symbol)
        except Exception as e:
            logger.error(f"RPC Error updating stock price for {symbol}: {e}")
            raise

class PriceSimulator:
    """Simulates stock price movements by updating MongoDB."""

    def __init__(self):
        self.running = True

    def start_simulation(self):
        """Start price simulation in background."""
        while self.running:
            try:
                stocks = list(stocks_collection.find({}))
                updated_count = 0

                for stock in stocks:
                    # Random price movement between -5% to +5%
                    change_percent = random.uniform(-0.05, 0.05)
                    new_price = stock['current_price'] * (1 + change_percent)
                    new_price = round(max(new_price, 1.0), 2)  # Minimum price $1

                    if new_price != stock['current_price']:
                        stocks_collection.update_one(
                            {'_id': stock['_id']},
                            {'$set': {'current_price': new_price, 'last_updated': datetime.utcnow()}}
                        )
                        updated_count += 1

                if updated_count > 0:
                    log_with_sync_time(logger, 20, f"Price simulation updated {updated_count} stocks", 'stock_exchange')

                time.sleep(10)  # Update every 10 seconds
            except Exception as e:
                logger.error(f"Error in price simulation: {e}")
                time.sleep(5)

    def stop_simulation(self):
        """Stop price simulation"""
        self.running = False

# Global price simulator
price_simulator = PriceSimulator()

# REST API Routes
@app.route('/stocks', methods=['GET'])
def get_all_stocks():
    """Get all stocks"""
    try:
        exchange_service = StockExchangeRPC()
        stocks_data = exchange_service.get_all_stocks()
        return jsonify({'stocks': stocks_data})
    except Exception as e:
        logger.error(f"Error getting all stocks: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/stocks/<symbol>', methods=['GET'])
def get_stock(symbol):
    """Get specific stock"""
    try:
        exchange_service = StockExchangeRPC()
        stock_data = exchange_service.get_stock(symbol.upper())
        return jsonify({'stock': stock_data})
    except StockNotFoundException as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error getting stock {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/stocks/<symbol>/price', methods=['GET'])
def get_stock_price(symbol):
    """Get stock price"""
    try:
        exchange_service = StockExchangeRPC()
        price = exchange_service.get_stock_price(symbol.upper())
        sync_time = log_with_sync_time(logger, 20, f"REST: Retrieved price for {symbol.upper()}", 'stock_exchange')

        return jsonify({
            'symbol': symbol.upper(),
            'price': price,
            'sync_time': sync_time
        })
    except StockNotFoundException as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error getting stock price for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/stocks/<symbol>/update', methods=['POST'])
def update_stock_price(symbol):
    """Update stock price"""
    try:
        data = request.json
        new_price = data.get('price')

        if not new_price or not isinstance(new_price, (int, float)) or new_price <= 0:
            return jsonify({'error': 'Valid positive price is required'}), 400

        exchange_service = StockExchangeRPC()
        updated_stock = exchange_service.update_stock_price(symbol.upper(), float(new_price))
        sync_time = log_with_sync_time(logger, 20, f"REST: Updated {symbol.upper()} price to {new_price}", 'stock_exchange')

        return jsonify({
            'message': 'Stock price updated successfully',
            'stock': updated_stock,
            'sync_time': sync_time
        })
    except StockNotFoundException as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error updating stock price for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/stocks/market/summary', methods=['GET'])
def get_market_summary():
    """Get market summary"""
    try:
        stocks = list(stocks_collection.find({}))

        if not stocks:
            return jsonify({'error': 'No stocks found'}), 404

        total_value = sum(stock['current_price'] for stock in stocks)
        avg_price = total_value / len(stocks)
        highest_price = max(stock['current_price'] for stock in stocks)
        lowest_price = min(stock['current_price'] for stock in stocks)

        summary = {
            'total_stocks': len(stocks),
            'total_market_value': round(total_value, 2),
            'average_price': round(avg_price, 2),
            'highest_price': highest_price,
            'lowest_price': lowest_price,
            'stocks': mongo_to_dict(stocks)
        }

        return jsonify({'market_summary': summary})
    except Exception as e:
        logger.error(f"Error getting market summary: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'stock_exchange_service'})

def start_pyro_server():
    """Start Pyro4 RPC server"""
    try:
        daemon = Pyro4.Daemon(host='localhost', port=9093)
        exchange_service_rpc = StockExchangeRPC()
        uri = daemon.register(exchange_service_rpc, "stockexchange")
        logger.info(f"Stock Exchange RPC ready. URI: {uri}")
        daemon.requestLoop()
    except Exception as e:
        logger.error(f"Error starting Pyro4 server: {e}")

def start_price_simulation():
    """Start price simulation"""
    try:
        logger.info("Starting price simulation...")
        price_simulator.start_simulation()
    except Exception as e:
        logger.error(f"Error in price simulation: {e}")

if __name__ == '__main__':
    # Start Pyro4 RPC server in background
    pyro_thread = threading.Thread(target=start_pyro_server, daemon=True)
    pyro_thread.start()

    # Start price simulation in background
    sim_thread = threading.Thread(target=start_price_simulation, daemon=True)
    sim_thread.start()

    # Register with time server
    try:
        config = load_config()
        time_server = Pyro4.Proxy(config.TIME_SERVER_URI)
        time_server.register_service('stock_exchange')
        logger.info("Registered with time server")
    except Exception as e:
        logger.warning(f"Could not register with time server: {e}")

    logger.info("Starting Stock Exchange Service on port 5003")
    app.run(host='0.0.0.0', port=5003, debug=True, use_reloader=False)
