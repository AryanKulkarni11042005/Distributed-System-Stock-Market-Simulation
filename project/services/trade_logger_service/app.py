from flask import Flask, jsonify, request
from flask_cors import CORS
import Pyro4
import threading
import json
import csv
import os
import sys
from datetime import datetime

# Add path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.config import load_config
from utils.logger import setup_logger, log_with_sync_time
from database.connection import init_db, db, Trade

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

# Initialize database
init_db(app)

# Create logs directory
os.makedirs('logs', exist_ok=True)

@Pyro4.expose
class TradeLoggerRPC:
    """Pyro4 RPC interface for Trade Logger Service"""
    
    def log_trade(self, user_id, stock_symbol, trade_type, quantity, price, total_amount, sync_timestamp=None):
        """Log a trade via RPC"""
        try:
            with app.app_context():
                trade = Trade(
                    user_id=user_id,
                    stock_symbol=stock_symbol,
                    trade_type=trade_type,
                    quantity=quantity,
                    price=price,
                    total_amount=total_amount,
                    sync_timestamp=sync_timestamp
                )
                db.session.add(trade)
                db.session.commit()
                
                # Also log to CSV for Spark analysis
                self._log_to_csv(trade)
                self._log_to_json(trade)
                
                log_with_sync_time(logger, 20, f"Logged trade: {trade_type} {quantity} {stock_symbol} for user {user_id}", 'trade_logger')
                return trade.to_dict()
        except Exception as e:
            logger.error(f"RPC Error logging trade: {e}")
            raise
    
    def get_trades_by_user(self, user_id):
        """Get all trades for a user via RPC"""
        try:
            with app.app_context():
                trades = Trade.query.filter_by(user_id=user_id).order_by(Trade.timestamp.desc()).all()
                return [trade.to_dict() for trade in trades]
        except Exception as e:
            logger.error(f"RPC Error getting trades for user {user_id}: {e}")
            raise
    
    def get_trades_by_stock(self, stock_symbol):
        """Get all trades for a stock via RPC"""
        try:
            with app.app_context():
                trades = Trade.query.filter_by(stock_symbol=stock_symbol).order_by(Trade.timestamp.desc()).all()
                return [trade.to_dict() for trade in trades]
        except Exception as e:
            logger.error(f"RPC Error getting trades for stock {stock_symbol}: {e}")
            raise
    
    def get_all_trades(self):
        """Get all trades via RPC"""
        try:
            with app.app_context():
                trades = Trade.query.order_by(Trade.timestamp.desc()).all()
                return [trade.to_dict() for trade in trades]
        except Exception as e:
            logger.error(f"RPC Error getting all trades: {e}")
            raise
    
    def _log_to_csv(self, trade):
        """Log trade to CSV file for Spark analysis"""
        try:
            csv_file = 'logs/trades.csv'
            file_exists = os.path.isfile(csv_file)
            
            with open(csv_file, 'a', newline='') as file:
                fieldnames = ['id', 'user_id', 'stock_symbol', 'trade_type', 'quantity', 'price', 'total_amount', 'timestamp', 'sync_timestamp']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow({
                    'id': trade.id,
                    'user_id': trade.user_id,
                    'stock_symbol': trade.stock_symbol,
                    'trade_type': trade.trade_type,
                    'quantity': trade.quantity,
                    'price': trade.price,
                    'total_amount': trade.total_amount,
                    'timestamp': trade.timestamp.isoformat(),
                    'sync_timestamp': trade.sync_timestamp
                })
        except Exception as e:
            logger.error(f"Error logging to CSV: {e}")
    
    def _log_to_json(self, trade):
        """Log trade to JSON file for Spark analysis"""
        try:
            json_file = 'logs/trades.json'
            
            trade_data = trade.to_dict()
            
            # Append to JSON file
            if os.path.exists(json_file):
                with open(json_file, 'r') as file:
                    try:
                        trades = json.load(file)
                    except json.JSONDecodeError:
                        trades = []
            else:
                trades = []
            
            trades.append(trade_data)
            
            with open(json_file, 'w') as file:
                json.dump(trades, file, indent=2)
                
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