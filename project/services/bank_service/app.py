from flask import Flask, jsonify, request
from flask_cors import CORS
import Pyro4
import threading
import sys
import os

# Add path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.config import load_config
from utils.logger import setup_logger, log_with_sync_time
from database.connection import init_db, db, BankAccount
from utils.exceptions import InsufficientFundsException

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

@Pyro4.expose
class BankServiceRPC:
    """Pyro4 RPC interface for Bank Service"""
    
    def get_balance(self, user_id):
        """Get account balance via RPC"""
        try:
            with app.app_context():
                account = BankAccount.query.filter_by(user_id=user_id).first()
                if not account:
                    # Create account with initial balance
                    config = load_config()
                    account = BankAccount(user_id=user_id, balance=config.INITIAL_BALANCE)
                    db.session.add(account)
                    db.session.commit()
                    log_with_sync_time(logger, 20, f"Created bank account for user {user_id}", 'bank_service')
                
                return account.balance
        except Exception as e:
            logger.error(f"RPC Error getting balance for user {user_id}: {e}")
            raise
    
    def debit_account(self, user_id, amount):
        """Debit amount from account via RPC"""
        try:
            with app.app_context():
                account = BankAccount.query.filter_by(user_id=user_id).first()
                if not account:
                    config = load_config()
                    account = BankAccount(user_id=user_id, balance=config.INITIAL_BALANCE)
                    db.session.add(account)
                    db.session.commit()
                
                if account.balance < amount:
                    raise InsufficientFundsException(f"Insufficient funds. Available: {account.balance}, Required: {amount}")
                
                account.balance -= amount
                db.session.commit()
                log_with_sync_time(logger, 20, f"Debited {amount} from user {user_id}", 'bank_service')
                return account.balance
        except Exception as e:
            logger.error(f"RPC Error debiting account for user {user_id}: {e}")
            raise
    
    def credit_account(self, user_id, amount):
        """Credit amount to account via RPC"""
        try:
            with app.app_context():
                account = BankAccount.query.filter_by(user_id=user_id).first()
                if not account:
                    config = load_config()
                    account = BankAccount(user_id=user_id, balance=config.INITIAL_BALANCE)
                    db.session.add(account)
                    db.session.commit()
                
                account.balance += amount
                db.session.commit()
                log_with_sync_time(logger, 20, f"Credited {amount} to user {user_id}", 'bank_service')
                return account.balance
        except Exception as e:
            logger.error(f"RPC Error crediting account for user {user_id}: {e}")
            raise
    
    def get_account(self, user_id):
        """Get full account details via RPC"""
        try:
            with app.app_context():
                account = BankAccount.query.filter_by(user_id=user_id).first()
                if not account:
                    config = load_config()
                    account = BankAccount(user_id=user_id, balance=config.INITIAL_BALANCE)
                    db.session.add(account)
                    db.session.commit()
                    log_with_sync_time(logger, 20, f"Created bank account for user {user_id}", 'bank_service')
                
                return account.to_dict()
        except Exception as e:
            logger.error(f"RPC Error getting account for user {user_id}: {e}")
            raise

# REST API Routes
@app.route('/bank/account/<int:user_id>', methods=['GET'])
def get_account(user_id):
    """Get bank account details"""
    try:
        bank_service = BankServiceRPC()
        account_data = bank_service.get_account(user_id)
        return jsonify({'account': account_data})
    except Exception as e:
        logger.error(f"Error getting account for user {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/bank/balance/<int:user_id>', methods=['GET'])
def get_balance(user_id):
    """Get account balance"""
    try:
        bank_service = BankServiceRPC()
        balance = bank_service.get_balance(user_id)
        return jsonify({'user_id': user_id, 'balance': balance})
    except Exception as e:
        logger.error(f"Error getting balance for user {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/bank/debit', methods=['POST'])
def debit_account():
    """Debit amount from account"""
    try:
        data = request.json
        user_id = data.get('user_id')
        amount = data.get('amount')
        
        if not user_id or not amount or amount <= 0:
            return jsonify({'error': 'Valid user_id and amount are required'}), 400
        
        bank_service = BankServiceRPC()
        new_balance = bank_service.debit_account(user_id, amount)
        sync_time = log_with_sync_time(logger, 20, f"REST: Debited {amount} from user {user_id}", 'bank_service')
        
        return jsonify({
            'message': 'Account debited successfully',
            'user_id': user_id,
            'amount_debited': amount,
            'new_balance': new_balance,
            'sync_time': sync_time
        })
    except InsufficientFundsException as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error debiting account: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/bank/credit', methods=['POST'])
def credit_account():
    """Credit amount to account"""
    try:
        data = request.json
        user_id = data.get('user_id')
        amount = data.get('amount')
        
        if not user_id or not amount or amount <= 0:
            return jsonify({'error': 'Valid user_id and amount are required'}), 400
        
        bank_service = BankServiceRPC()
        new_balance = bank_service.credit_account(user_id, amount)
        sync_time = log_with_sync_time(logger, 20, f"REST: Credited {amount} to user {user_id}", 'bank_service')
        
        return jsonify({
            'message': 'Account credited successfully',
            'user_id': user_id,
            'amount_credited': amount,
            'new_balance': new_balance,
            'sync_time': sync_time
        })
    except Exception as e:
        logger.error(f"Error crediting account: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'bank_service'})

def start_pyro_server():
    """Start Pyro4 RPC server"""
    try:
        daemon = Pyro4.Daemon(host='localhost', port=9092)
        bank_service_rpc = BankServiceRPC()
        uri = daemon.register(bank_service_rpc, "bankservice")
        logger.info(f"Bank Service RPC ready. URI: {uri}")
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
        time_server.register_service('bank_service')
        logger.info("Registered with time server")
    except Exception as e:
        logger.warning(f"Could not register with time server: {e}")
    
    logger.info("Starting Bank Service on port 5002")
    app.run(host='0.0.0.0', port=5002, debug=True, use_reloader=False)