from flask import Flask, Blueprint, request, jsonify
from flask_cors import CORS
import Pyro4
import threading
import sys
import os
from datetime import datetime
from bson import json_util, ObjectId
import json
from werkzeug.security import generate_password_hash, check_password_hash

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.config import load_config
from utils.logger import setup_logger, log_with_sync_time
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
init_db()

def mongo_to_dict(obj):
    return json.loads(json_util.dumps(obj))

class UserService:
    @staticmethod
    def create_user(username, email, password):
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        user_document = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "role": "user",
            "created_at": datetime.utcnow()
        }
        result = users_collection.insert_one(user_document)
        
        # Create a corresponding portfolio for the new user
        portfolio_collection.insert_one({
            "user_id": result.inserted_id,
            "holdings": []
        })

        log_with_sync_time(logger, 20, f"Created user: {username}", 'user_service')
        user_document['_id'] = result.inserted_id
        return user_document

    @staticmethod
    def get_user(user_id):
        return users_collection.find_one({'_id': ObjectId(user_id)})

    @staticmethod
    def get_user_by_username(username):
        return users_collection.find_one({'username': username})

    @staticmethod
    def get_user_portfolio(user_id):
        return portfolio_collection.find_one({'user_id': ObjectId(user_id)})

    @staticmethod
    def update_portfolio(user_id, stock_symbol, quantity, price, trade_type):
        user_oid = ObjectId(user_id)
        portfolio = portfolio_collection.find_one({'user_id': user_oid})
        
        if not portfolio:
            raise UserNotFoundException(f"Portfolio not found for user {user_id}")

        holding_index = -1
        for i, holding in enumerate(portfolio.get('holdings', [])):
            if holding['stock_symbol'] == stock_symbol:
                holding_index = i
                break

        if trade_type == 'buy':
            if holding_index != -1:
                # Update existing holding
                current_quantity = portfolio['holdings'][holding_index]['quantity']
                current_avg_price = portfolio['holdings'][holding_index]['avg_price']
                
                total_value = (current_quantity * current_avg_price) + (quantity * price)
                new_quantity = current_quantity + quantity
                new_avg_price = total_value / new_quantity

                portfolio_collection.update_one(
                    {'user_id': user_oid, 'holdings.stock_symbol': stock_symbol},
                    {'$set': {
                        f'holdings.{holding_index}.quantity': new_quantity,
                        f'holdings.{holding_index}.avg_price': new_avg_price
                    }}
                )
            else:
                # Add new holding
                new_holding = {
                    'stock_symbol': stock_symbol,
                    'quantity': quantity,
                    'avg_price': price
                }
                portfolio_collection.update_one(
                    {'user_id': user_oid},
                    {'$push': {'holdings': new_holding}}
                )
        
        elif trade_type == 'sell':
            if holding_index != -1:
                current_quantity = portfolio['holdings'][holding_index]['quantity']
                if current_quantity >= quantity:
                    new_quantity = current_quantity - quantity
                    if new_quantity == 0:
                        # Remove the holding if quantity is zero
                        portfolio_collection.update_one(
                            {'user_id': user_oid},
                            {'$pull': {'holdings': {'stock_symbol': stock_symbol}}}
                        )
                    else:
                        # Otherwise, just decrement the quantity
                        portfolio_collection.update_one(
                            {'user_id': user_oid, 'holdings.stock_symbol': stock_symbol},
                            {'$set': {f'holdings.{holding_index}.quantity': new_quantity}}
                        )
                else:
                    raise InsufficientStocksException(f"Insufficient stocks to sell. Available: {current_quantity}, Required: {quantity}")
            else:
                raise InsufficientStocksException("Cannot sell stock that is not in the portfolio.")
        
        log_with_sync_time(logger, 20, f"Updated portfolio for user {user_id}: {trade_type} {quantity} {stock_symbol}", 'user_service')
        return portfolio_collection.find_one({'user_id': user_oid})


@Pyro4.expose
class UserServiceRPC:
    def create_user(self, username, email, password):
        try:
            user = UserService.create_user(username, email, password)
            return mongo_to_dict(user)
        except Exception as e:
            logger.error(f"RPC Error creating user: {e}")
            raise
    
    def get_user(self, user_id):
        try:
            user = UserService.get_user(user_id)
            return mongo_to_dict(user) if user else None
        except Exception as e:
            logger.error(f"RPC Error getting user {user_id}: {e}")
            raise
    
    def get_user_portfolio(self, user_id):
        try:
            portfolio = UserService.get_user_portfolio(user_id)
            return mongo_to_dict(portfolio)
        except Exception as e:
            logger.error(f"RPC Error getting portfolio for user {user_id}: {e}")
            raise
    
    def update_portfolio(self, user_id, stock_symbol, quantity, price, trade_type):
        try:
            portfolio_item = UserService.update_portfolio(user_id, stock_symbol, quantity, price, trade_type)
            return mongo_to_dict(portfolio_item) if portfolio_item else None
        except Exception as e:
            logger.error(f"RPC Error updating portfolio: {e}")
            raise

user_bp = Blueprint('user', __name__)

@user_bp.route('/create', methods=['POST'])
def create_user():
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        if UserService.get_user_by_username(username):
            return jsonify({'error': 'Username already exists'}), 400
        
        user = UserService.create_user(username, email, password)
        sync_time = log_with_sync_time(logger, 20, f"REST: Created user {username}", 'user_service')
        
        user.pop('password', None)

        return jsonify({
            'message': 'User created successfully',
            'user': mongo_to_dict(user),
            'sync_time': sync_time
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({'error': str(e)}), 500

@user_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        user = UserService.get_user_by_username(username)

        if not user or not check_password_hash(user['password'], password):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        user.pop('password', None)
        return jsonify({
            'message': 'Login successful',
            'user': mongo_to_dict(user)
        })

    except Exception as e:
        logger.error(f"Error during login for user {username}: {e}")
        return jsonify({'error': 'An internal error occurred'}), 500

@user_bp.route('/<string:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = UserService.get_user(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.pop('password', None)
        return jsonify({'user': mongo_to_dict(user)})
        
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

@user_bp.route('/<string:user_id>/portfolio', methods=['GET'])
def get_portfolio(user_id):
    try:
        portfolio = UserService.get_user_portfolio(user_id)
        
        return jsonify({
            'user_id': user_id,
            'portfolio': mongo_to_dict(portfolio) if portfolio else {'holdings': []}
        })
        
    except Exception as e:
        logger.error(f"Error getting portfolio for user {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

@user_bp.route('/<string:user_id>/portfolio/update', methods=['POST'])
def update_portfolio(user_id):
    try:
        data = request.json
        stock_symbol = data.get('stock_symbol')
        quantity = data.get('quantity')
        price = data.get('price')
        trade_type = data.get('trade_type')
        
        if not all([stock_symbol, isinstance(quantity, int), isinstance(price, (int, float)), trade_type]):
            return jsonify({'error': 'All fields with correct types are required'}), 400
        
        updated_portfolio = UserService.update_portfolio(
            user_id, stock_symbol, quantity, price, trade_type
        )
        
        sync_time = log_with_sync_time(logger, 20, f"REST: Updated portfolio for user {user_id}", 'user_service')
        
        return jsonify({
            'message': 'Portfolio updated successfully',
            'portfolio': mongo_to_dict(updated_portfolio) if updated_portfolio else None,
            'sync_time': sync_time
        })
        
    except (InsufficientStocksException, UserNotFoundException) as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating portfolio for user {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

app.register_blueprint(user_bp, url_prefix='/user')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'user_service'})

def start_pyro_server():
    try:
        daemon = Pyro4.Daemon(host='localhost', port=9091)
        user_service_rpc = UserServiceRPC()
        uri = daemon.register(user_service_rpc, "userservice")
        logger.info(f"User Service RPC ready. URI: {uri}")
        daemon.requestLoop()
    except Exception as e:
        logger.error(f"Error starting Pyro4 server: {e}")

if __name__ == '__main__':
    pyro_thread = threading.Thread(target=start_pyro_server, daemon=True)
    pyro_thread.start()
    
    try:
        config = load_config()
        time_server = Pyro4.Proxy(config.TIME_SERVER_URI)
        time_server.register_service('user_service')
        logger.info("Registered with time server")
    except Exception as e:
        logger.warning(f"Could not register with time server: {e}")
    
    logger.info("Starting User Service on port 5001")
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)