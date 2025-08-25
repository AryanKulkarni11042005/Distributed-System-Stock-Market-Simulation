import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime
import urllib.parse

# It's a good practice to load sensitive information from environment variables.
# Fallback to the provided connection string if the environment variable isn't set.
MONGO_USER = os.getenv('MONGO_USER', 'aryankulkarni1104')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'Aryan@2005')
MONGO_CLUSTER = os.getenv('MONGO_CLUSTER', 'cluster0.qxaih.mongodb.net')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'stock_market_simulation')

# URL-encode the password to handle special characters
encoded_password = urllib.parse.quote_plus(MONGO_PASSWORD)

# Construct the connection string
MONGO_URI = f"mongodb+srv://{MONGO_USER}:{encoded_password}@{MONGO_CLUSTER}/{MONGO_DB_NAME}?retryWrites=true&w=majority"

class MongoConnection:
    """
    Singleton class to manage MongoDB connection.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoConnection, cls).__new__(cls)
            try:
                cls._instance.client = MongoClient(MONGO_URI)
                # The ismaster command is cheap and does not require auth.
                cls._instance.client.admin.command('ismaster')
                print("MongoDB connection successful.")
                cls._instance.db = cls._instance.client[MONGO_DB_NAME]
            except ConnectionFailure as e:
                print(f"Could not connect to MongoDB: {e}")
                cls._instance.client = None
                cls._instance.db = None
        return cls._instance

# Initialize the connection
mongo_conn = MongoConnection()
db = mongo_conn.db

# Define collections for easy access throughout the application
if db is not None:
    users_collection = db.users
    portfolio_collection = db.portfolio
    bank_accounts_collection = db.bank_accounts
    stocks_collection = db.stocks
    trades_collection = db.trades
else:
    # If connection fails, create dummy objects to prevent crashes on import
    users_collection = None
    portfolio_collection = None
    bank_accounts_collection = None
    stocks_collection = None
    trades_collection = None


def init_db(app=None):
    """
    Initializes the database with sample data.
    """
    if db is not None:
        print("Initializing sample data...")
        init_sample_data()
    else:
        print("Skipping sample data initialization due to connection failure.")


def init_sample_data():
    """
    Initializes the stocks collection with sample data if it's empty.
    """
    if stocks_collection is None:
        print("Stock collection not available.")
        return

    sample_stocks = [
        {'symbol': 'AAPL', 'name': 'Apple Inc.', 'current_price': 150.00, 'last_updated': datetime.utcnow()},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'current_price': 2800.00, 'last_updated': datetime.utcnow()},
        {'symbol': 'MSFT', 'name': 'Microsoft Corporation', 'current_price': 300.00, 'last_updated': datetime.utcnow()},
        {'symbol': 'TSLA', 'name': 'Tesla Inc.', 'current_price': 800.00, 'last_updated': datetime.utcnow()},
        {'symbol': 'AMZN', 'name': 'Amazon.com Inc.', 'current_price': 3300.00, 'last_updated': datetime.utcnow()},
    ]

    try:
        for stock in sample_stocks:
            stocks_collection.update_one(
                {'symbol': stock['symbol']},
                {'$setOnInsert': stock},
                upsert=True
            )
        print("Sample stock data initialized successfully.")
    except Exception as e:
        print(f"Error initializing sample data: {e}")