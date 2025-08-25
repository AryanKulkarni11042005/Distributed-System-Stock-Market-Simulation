from flask import Flask, jsonify, request
from flask_cors import CORS
import Pyro4
import threading
import sys
import os
from datetime import datetime
from bson import json_util, ObjectId
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.config import load_config
from utils.logger import setup_logger, log_with_sync_time
from database.connection import init_db, bank_accounts_collection, users_collection
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
init_db()

def mongo_to_dict(obj):
    return json.loads(json_util.dumps(obj))

@Pyro4.expose
class BankServiceRPC:
    def _get_or_create_account(self, user_id):
        user_oid = ObjectId(user_id)
        account = bank_accounts_collection.find_one({'user_id': user_oid})
        if not account:
            if not users_collection.find_one({'_id': user_oid}):
                raise Exception(f"User with ID {user_id} not found.")

            config = load_config()
            new_account = {
                'user_id': user_oid,
                'balance': config.INITIAL_BALANCE,
                'transactions': [],
                'created_at': datetime.utcnow()
            }
            bank_accounts_collection.insert_one(new_account)
            log_with_sync_time(logger, 20, f"Created bank account for user {user_id}", 'bank_service')
            return new_account
        return account

    def get_balance(self, user_id):
        try:
            account = self._get_or_create_account(user_id)
            return account['balance']
        except Exception as e:
            logger.error(f"RPC Error getting balance for user {user_id}: {e}")
            raise

    def debit_account(self, user_id, amount):
        try:
            account = self._get_or_create_account(user_id)
            if account['balance'] < amount:
                raise InsufficientFundsException(f"Insufficient funds. Available: {account['balance']}, Required: {amount}")

            transaction = {
                'type': 'debit',
                'amount': amount,
                'timestamp': datetime.utcnow()
            }
            result = bank_accounts_collection.update_one(
                {'user_id': ObjectId(user_id)},
                {
                    '$inc': {'balance': -amount},
                    '$push': {'transactions': transaction}
                }
            )

            if result.modified_count == 0:
                 raise Exception("Failed to debit account.")

            log_with_sync_time(logger, 20, f"Debited {amount} from user {user_id}", 'bank_service')
            return self.get_balance(user_id)
        except Exception as e:
            logger.error(f"RPC Error debiting account for user {user_id}: {e}")
            raise

    def credit_account(self, user_id, amount):
        try:
            self._get_or_create_account(user_id)
            
            transaction = {
                'type': 'credit',
                'amount': amount,
                'timestamp': datetime.utcnow()
            }
            result = bank_accounts_collection.update_one(
                {'user_id': ObjectId(user_id)},
                {
                    '$inc': {'balance': amount},
                    '$push': {'transactions': transaction}
                }
            )

            if result.modified_count == 0:
                 raise Exception("Failed to credit account.")

            log_with_sync_time(logger, 20, f"Credited {amount} to user {user_id}", 'bank_service')
            return self.get_balance(user_id)
        except Exception as e:
            logger.error(f"RPC Error crediting account for user {user_id}: {e}")
            raise

    def get_account(self, user_id):
        try:
            account = self._get_or_create_account(user_id)
            return mongo_to_dict(account)
        except Exception as e:
            logger.error(f"RPC Error getting account for user {user_id}: {e}")
            raise

@app.route('/bank/account/<string:user_id>', methods=['GET'])
def get_account(user_id):
    try:
        bank_service = BankServiceRPC()
        account_data = bank_service.get_account(user_id)
        return jsonify({'account': account_data})
    except Exception as e:
        logger.error(f"Error getting account for user {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/bank/balance/<string:user_id>', methods=['GET'])
def get_balance(user_id):
    try:
        bank_service = BankServiceRPC()
        balance = bank_service.get_balance(user_id)
        return jsonify({'user_id': user_id, 'balance': balance})
    except Exception as e:
        logger.error(f"Error getting balance for user {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/bank/debit', methods=['POST'])
def debit_account():
    try:
        data = request.json
        user_id = data.get('user_id')
        amount = data.get('amount')

        if not user_id or not isinstance(amount, (int, float)) or amount <= 0:
            return jsonify({'error': 'Valid user_id and a positive amount are required'}), 400

        bank_service = BankServiceRPC()
        new_balance = bank_service.debit_account(user_id, float(amount))
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
    try:
        data = request.json
        user_id = data.get('user_id')
        amount = data.get('amount')

        if not user_id or not isinstance(amount, (int, float)) or amount <= 0:
            return jsonify({'error': 'Valid user_id and a positive amount are required'}), 400

        bank_service = BankServiceRPC()
        new_balance = bank_service.credit_account(user_id, float(amount))
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
    try:
        daemon = Pyro4.Daemon(host='localhost', port=9092)
        bank_service_rpc = BankServiceRPC()
        uri = daemon.register(bank_service_rpc, "bankservice")
        logger.info(f"Bank Service RPC ready. URI: {uri}")
        daemon.requestLoop()
    except Exception as e:
        logger.error(f"Error starting Pyro4 server: {e}")

if __name__ == '__main__':
    pyro_thread = threading.Thread(target=start_pyro_server, daemon=True)
    pyro_thread.start()

    try:
        config = load_config()
        time_server = Pyro4.Proxy(config.TIME_SERVER_URI)
        time_server.register_service('bank_service')
        logger.info("Registered with time server")
    except Exception as e:
        logger.warning(f"Could not register with time server: {e}")

    logger.info("Starting Bank Service on port 5002")
    app.run(host='0.0.0.0', port=5002, debug=True, use_reloader=False)