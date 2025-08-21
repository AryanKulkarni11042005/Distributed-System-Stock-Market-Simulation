from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }

class Portfolio(db.Model):
    __tablename__ = 'portfolio'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stock_symbol = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    avg_price = db.Column(db.Float, nullable=False, default=0.0)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'stock_symbol'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'stock_symbol': self.stock_symbol,
            'quantity': self.quantity,
            'avg_price': self.avg_price
        }

class BankAccount(db.Model):
    __tablename__ = 'bank_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, unique=True)
    balance = db.Column(db.Float, nullable=False, default=10000.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'balance': self.balance,
            'created_at': self.created_at.isoformat()
        }

class Stock(db.Model):
    __tablename__ = 'stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'name': self.name,
            'current_price': self.current_price,
            'last_updated': self.last_updated.isoformat()
        }

class Trade(db.Model):
    __tablename__ = 'trades'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    stock_symbol = db.Column(db.String(10), nullable=False)
    trade_type = db.Column(db.String(10), nullable=False)  # 'buy' or 'sell'
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    sync_timestamp = db.Column(db.String(50))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'stock_symbol': self.stock_symbol,
            'trade_type': self.trade_type,
            'quantity': self.quantity,
            'price': self.price,
            'total_amount': self.total_amount,
            'timestamp': self.timestamp.isoformat(),
            'sync_timestamp': self.sync_timestamp
        }

def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        # Initialize sample data
        init_sample_data()

def init_sample_data():
    """Initialize sample stocks"""
    sample_stocks = [
        ('AAPL', 'Apple Inc.', 150.00),
        ('GOOGL', 'Alphabet Inc.', 2800.00),
        ('MSFT', 'Microsoft Corporation', 300.00),
        ('TSLA', 'Tesla Inc.', 800.00),
        ('AMZN', 'Amazon.com Inc.', 3300.00),
    ]
    
    for symbol, name, price in sample_stocks:
        if not Stock.query.filter_by(symbol=symbol).first():
            stock = Stock(symbol=symbol, name=name, current_price=price)
            db.session.add(stock)
    
    db.session.commit()