import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///stock_market.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Service URLs
    USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://localhost:5001')
    BANK_SERVICE_URL = os.getenv('BANK_SERVICE_URL', 'http://localhost:5002')
    STOCK_EXCHANGE_URL = os.getenv('STOCK_EXCHANGE_URL', 'http://localhost:5003')
    TRADE_LOGGER_URL = os.getenv('TRADE_LOGGER_URL', 'http://localhost:5004')
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5000')
    
    # Pyro4 Configuration
    PYRO_HOST = os.getenv('PYRO_HOST', 'localhost')
    PYRO_PORT = int(os.getenv('PYRO_PORT', 9090))
    TIME_SERVER_URI = os.getenv('TIME_SERVER_URI', 'PYRO:timeserver@localhost:9090')
    
    # Business Logic
    INITIAL_BALANCE = float(os.getenv('INITIAL_BALANCE', 10000.0))

def load_config():
    return Config