from flask import Flask, jsonify, request
from flask_cors import CORS
import Pyro4
import threading
import json
import csv
import os
import sys
from datetime import datetime
from bson import json_util

# Add path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.config import load_config
from utils.logger import setup_logger, log_with_sync_time
# Import the MongoDB collections from the updated connection script
from database.connection import init_db, trades_collection
from pymongo import DESCENDING

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

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

def mongo_to_dict(obj):
    """
    Helper function to convert MongoDB documents (including ObjectId) to a JSON-serializable dictionary.
    """
    return json.loads(json_util.dumps(obj))

@Pyro4.expose
class TradeLoggerRPC:
    """Pyro4 RPC interface for Trade Logger Service, now using MongoDB."""

    def log_trade(self, user_id, stock_symbol, trade_type, quantity, price, total_amount, sync_timestamp=None):
        """Log a trade via RPC to MongoDB."""
        try:
            trade_document = {
                'user_id': user_id,
                'stock_symbol': stock_symbol,
                'trade_type': trade_type,
                'quantity': quantity,
                'price': price,
                'total_amount': total_amount,
                'timestamp': datetime.utcnow(),
                'sync_timestamp': sync_timestamp
            }
            result = trades_collection.insert_one(trade_document)
            
            # Add the generated _id to the document for logging and return
            trade_document['_id'] = result.inserted_id

            # Also log to CSV and JSON for Spark analysis
            self._log_to_csv(trade_document)
            self._log_to_json(trade_document)

            log_with_sync_time(logger, 20, f"Logged trade: {trade_type} {quantity} {stock_symbol} for user {user_id}", 'trade_logger')
            return mongo_to_dict(trade_document)
        except Exception as e:
            logger.error(f"RPC Error logging trade: {e}")
            raise

    def get_trades_by_user(self, user_id):
        """Get all trades for a user via RPC from MongoDB."""
        try:
            trades = list(trades_collection.find({'user_id': user_id}).sort('timestamp', DESCENDING))
            return mongo_to_dict(trades)
        except Exception as e:
            logger.error(f"RPC Error getting trades for user {user_id}: {e}")
            raise

    def get_trades_by_stock(self, stock_symbol):
        """Get all trades for a stock via RPC from MongoDB."""
        try:
            trades = list(trades_collection.find({'stock_symbol': stock_symbol}).sort('timestamp', DESCENDING))
            return mongo_to_dict(trades)
        except Exception as e:
            logger.error(f"RPC Error getting trades for stock {stock_symbol}: {e}")
            raise

    def get_all_trades(self):
        """Get all trades via RPC from MongoDB."""
        try:
            trades = list(trades_collection.find({}).sort('timestamp', DESCENDING))
            return mongo_to_dict(trades)
        except Exception as e:
            logger.error(f"RPC Error getting all trades: {e}")
            raise

    def _log_to_csv(self, trade):
        """Log trade to CSV file for Spark analysis."""
        try:
            csv_file = 'logs/trades.csv'
            file_exists = os.path.isfile(csv_file)

            with open(csv_file, 'a', newline='') as file:
                # Note: MongoDB's '_id' is used as the primary identifier 'id'
                fieldnames = ['id', 'user_id', 'stock_symbol', 'trade_type', 'quantity', 'price', 'total_amount', 'timestamp', 'sync_timestamp']
                writer = csv.DictWriter(file, fieldnames=fieldnames)

                if not file_exists:
                    writer.writeheader()

                writer.writerow({
                    'id': str(trade['_id']),
                    'user_id': trade['user_id'],
                    'stock_symbol': trade['stock_symbol'],
                    'trade_type': trade['trade_type'],
                    'quantity': trade['quantity'],
                    'price': trade['price'],
                    'total_amount': trade['total_amount'],
                    'timestamp': trade['timestamp'].isoformat(),
                    'sync_timestamp': trade['sync_timestamp']
                })
        except Exception as e:
            logger.error(f"Error logging to CSV: {e}")

    def _log_to_json(self, trade):
        """Log trade to JSON file for Spark analysis."""
        try:
            json_file = 'logs/trades.json'
            
            trade_data = mongo_to_dict(trade)

            if os.path.exists(json_file) and os.path.getsize(json_file) > 0:
                with open(json_file, 'r+') as file:
                    try:
                        trades = json.load(file)
                    except json.JSONDecodeError:
                        trades = []
                    
                    trades.append(trade_data)
                    file.seek(0)
                    json.dump(trades, file, indent=2)
            else:
                with open(json_file, 'w') as file:
                    json.dump([trade_data], file, indent=2)

        except Exception as e:
            logger.error(f"Error logging to JSON: {e}")

# REST API Routes
@app.route('/trade/log', methods=['POST'])
def log_trade():
    """Log a trade"""
    try:
        data = request.json
        user_id = data.get('user_id')
        stock_symbol = data.get('stock_symbol')
        trade_type = data.get('trade_type')
        quantity = data.get('quantity')
        price = data.get('price')
        total_amount = data.get('total_amount')
        sync_timestamp = data.get('sync_timestamp')

        if not all([user_id, stock_symbol, trade_type, quantity, price, total_amount]):
            return jsonify({'error': 'All trade fields are required'}), 400

        trade_logger = TradeLoggerRPC()
        trade_data = trade_logger.log_trade(user_id, stock_symbol, trade_type, quantity, price, total_amount, sync_timestamp)

        return jsonify({
            'message': 'Trade logged successfully',
            'trade': trade_data
        }), 201
    except Exception as e:
        logger.error(f"Error logging trade: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/trade/user/<int:user_id>', methods=['GET'])
def get_user_trades(user_id):
    """Get trades for a user"""
    try:
        trade_logger = TradeLoggerRPC()
        trades = trade_logger.get_trades_by_user(user_id)
        return jsonify({'user_id': user_id, 'trades': trades})
    except Exception as e:
        logger.error(f"Error getting trades for user {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/trade/stock/<symbol>', methods=['GET'])
def get_stock_trades(symbol):
    """Get trades for a stock"""
    try:
        trade_logger = TradeLoggerRPC()
        trades = trade_logger.get_trades_by_stock(symbol.upper())
        return jsonify({'stock_symbol': symbol.upper(), 'trades': trades})
    except Exception as e:
        logger.error(f"Error getting trades for stock {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/trade/all', methods=['GET'])
def get_all_trades():
    """Get all trades"""
    try:
        trade_logger = TradeLoggerRPC()
        trades = trade_logger.get_all_trades()
        return jsonify({'trades': trades})
    except Exception as e:
        logger.error(f"Error getting all trades: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'trade_logger_service'})

def start_pyro_server():
    """Start Pyro4 RPC server"""
    try:
        daemon = Pyro4.Daemon(host='localhost', port=9094)
        trade_logger_rpc = TradeLoggerRPC()
        uri = daemon.register(trade_logger_rpc, "tradelogger")
        logger.info(f"Trade Logger RPC ready. URI: {uri}")
        daemon.requestLoop()
    except Exception as e:
        logger.error(f"Error starting Pyro4 server: {e}")

if __name__ == '__main__':
    # Start Pyro4 RPC server in background
    pyro_thread = threading.Thread(target=start_pyro_server, daemon=True)
    pyro_thread.start()

    # Register with time server
    try:
        config = load_config()
        time_server = Pyro4.Proxy(config.TIME_SERVER_URI)
        time_server.register_service('trade_logger')
        logger.info("Registered with time server")
    except Exception as e:
        logger.warning(f"Could not register with time server: {e}")

    logger.info("Starting Trade Logger Service on port 5004")
    app.run(host='0.0.0.0', port=5004, debug=True, use_reloader=False)
