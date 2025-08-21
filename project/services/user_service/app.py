from flask import Flask, Blueprint, request, jsonify
from flask_cors import CORS
import Pyro4
import threading
import sys
import os
from datetime import datetime
from bson import json_util, ObjectId
import json

# Add path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.config import load_config
from utils.logger import setup_logger, log_with_sync_time
# Import the MongoDB collections
from database.connection import init_db, users_collection, portfolio_collection
from utils.exceptions import UserNotFoundException, InsufficientStocksException

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
init_db()

def mongo_to_dict(obj):
    """Helper to convert MongoDB documents to JSON-serializable dicts."""
    return json.loads(json_util.dumps(obj))

# User Service Logic
class UserService:
    @staticmethod
    def create_user(username, email):
        """Create a new user in MongoDB."""
        user_document = {
            "username": username,
            "email": email,
            "created_at": datetime.utcnow()
        }
        result = users_collection.insert_one(user_document)
        log_with_sync_time(logger, 20, f"Created user: {username}", 'user_service')
        user_document['_id'] = result.inserted_id
        return user_document

    @staticmethod
    def get_user(user_id):
        """Get user by ID from MongoDB."""
        # ObjectId is required for querying by _id
        return users_collection.find_one({'_id': ObjectId(user_id)})

    @staticmethod
    def get_user_by_username(username):
        """Get user by username from MongoDB."""
        return users_collection.find_one({'username': username})

    @staticmethod
    def get_user_portfolio(user_id):
        """Get user's portfolio from MongoDB."""
        return list(portfolio_collection.find({'user_id': user_id}))

    @staticmethod
    def update_portfolio(user_id, stock_symbol, quantity, price, trade_type):
        """Update user's portfolio in MongoDB."""
        query = {'user_id': user_id, 'stock_symbol': stock_symbol}
        portfolio_item = portfolio_collection.find_one(query)

        if trade_type == 'buy':
            if portfolio_item:
                # Update existing holding
                total_value = (portfolio_item['quantity'] * portfolio_item['avg_price']) + (quantity * price)
                new_quantity = portfolio_item['quantity'] + quantity
                new_avg_price = total_value / new_quantity
                
                update = {
                    '$set': {
                        'quantity': new_quantity,
                        'avg_price': new_avg_price
                    }
                }
                portfolio_collection.update_one(query, update)
            else:
                # Create new holding
                new_item = {
                    'user_id': user_id,
                    'stock_symbol': stock_symbol,
                    'quantity': quantity,
                    'avg_price': price
                }
                portfolio_collection.insert_one(new_item)
        
        elif trade_type == 'sell':
            if portfolio_item and portfolio_item['quantity'] >= quantity:
                new_quantity = portfolio_item['quantity'] - quantity
                if new_quantity == 0:
                    # If quantity is zero, remove the item from portfolio
                    portfolio_collection.delete_one(query)
                else:
                    # Otherwise, just decrement the quantity
                    portfolio_collection.update_one(query, {'$inc': {'quantity': -quantity}})
            else:
                available_qty = portfolio_item['quantity'] if portfolio_item else 0
                raise InsufficientStocksException(f"Insufficient stocks to sell. Available: {available_qty}, Required: {quantity}")
        
        log_with_sync_time(logger, 20, f"Updated portfolio for user {user_id}: {trade_type} {quantity} {stock_symbol}", 'user_service')
        return portfolio_collection.find_one(query)

@Pyro4.expose
class UserServiceRPC:
    """Pyro4 RPC interface for User Service, now using MongoDB."""
    
    def create_user(self, username, email):
        """Create a new user via RPC."""
        try:
            user = UserService.create_user(username, email)
            return mongo_to_dict(user)
        except Exception as e:
            logger.error(f"RPC Error creating user: {e}")
            raise
    
    def get_user(self, user_id):
        """Get user by ID via RPC."""
        try:
            user = UserService.get_user(user_id)
            return mongo_to_dict(user) if user else None
        except Exception as e:
            logger.error(f"RPC Error getting user {user_id}: {e}")
            raise
    
    def get_user_portfolio(self, user_id):
        """Get user's portfolio via RPC."""
        try:
            portfolio = UserService.get_user_portfolio(user_id)
            return mongo_to_dict(portfolio)
        except Exception as e:
            logger.error(f"RPC Error getting portfolio for user {user_id}: {e}")
            raise
    
    def update_portfolio(self, user_id, stock_symbol, quantity, price, trade_type):
        """Update user's portfolio via RPC."""
        try:
            portfolio_item = UserService.update_portfolio(user_id, stock_symbol, quantity, price, trade_type)
            return mongo_to_dict(portfolio_item) if portfolio_item else None
        except Exception as e:
            logger.error(f"RPC Error updating portfolio: {e}")
            raise

# Create Blueprint for REST API
user_bp = Blueprint('user', __name__)

@user_bp.route('/create', methods=['POST'])
def create_user():
    """Create a new user"""
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        
        if not username or not email:
            return jsonify({'error': 'Username and email are required'}), 400
        
        if UserService.get_user_by_username(username):
            return jsonify({'error': 'Username already exists'}), 400
        
        user = UserService.create_user(username, email)
        sync_time = log_with_sync_time(logger, 20, f"REST: Created user {username}", 'user_service')
        
        return jsonify({
            'message': 'User created successfully',
            'user': mongo_to_dict(user),
            'sync_time': sync_time
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({'error': str(e)}), 500

@user_bp.route('/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID"""
    try:
        user = UserService.get_user(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': mongo_to_dict(user)})
        
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

@user_bp.route('/<int:user_id>/portfolio', methods=['GET'])
def get_portfolio(user_id):
    """Get user's portfolio"""
    try:
        # Check if user exists (optional, but good practice)
        # For this, we need a way to query by integer ID if that's what's passed
        # Assuming user_id in portfolio is the same int
        
        portfolio = UserService.get_user_portfolio(user_id)
        
        return jsonify({
            'user_id': user_id,
            'portfolio': mongo_to_dict(portfolio)
        })
        
    except Exception as e:
        logger.error(f"Error getting portfolio for user {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

@user_bp.route('/<int:user_id>/portfolio/update', methods=['POST'])
def update_portfolio(user_id):
    """Update user's portfolio"""
    try:
        data = request.json
        stock_symbol = data.get('stock_symbol')
        quantity = data.get('quantity')
        price = data.get('price')
        trade_type = data.get('trade_type')
        
        if not all([stock_symbol, isinstance(quantity, int), isinstance(price, (int, float)), trade_type]):
            return jsonify({'error': 'All fields with correct types are required'}), 400
        
        portfolio_item = UserService.update_portfolio(
            user_id, stock_symbol, quantity, price, trade_type
        )
        
        sync_time = log_with_sync_time(logger, 20, f"REST: Updated portfolio for user {user_id}", 'user_service')
        
        return jsonify({
            'message': 'Portfolio updated successfully',
            'portfolio_item': mongo_to_dict(portfolio_item) if portfolio_item else None,
            'sync_time': sync_time
        })
        
    except InsufficientStocksException as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating portfolio for user {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

# Register blueprint
app.register_blueprint(user_bp, url_prefix='/user')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'user_service'})

def start_pyro_server():
    """Start Pyro4 RPC server in background thread"""
    try:
        daemon = Pyro4.Daemon(host='localhost', port=9091)
        user_service_rpc = UserServiceRPC()
        uri = daemon.register(user_service_rpc, "userservice")
        logger.info(f"User Service RPC ready. URI: {uri}")
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
        time_server.register_service('user_service')
        logger.info("Registered with time server")
    except Exception as e:
        logger.warning(f"Could not register with time server: {e}")
    
    logger.info("Starting User Service on port 5001")
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
