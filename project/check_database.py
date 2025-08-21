import sqlite3
import os
from datetime import datetime

def check_database():
    """Check the stock_market.db database"""
    
    db_path = 'instance/stock_market.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return
    
    print(f"✅ Found database at: {db_path}")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📊 Database Tables: {len(tables)}")
        print("-" * 30)
        
        for table in tables:
            table_name = table[0]
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            print(f"\n📋 Table: {table_name}")
            print(f"   Rows: {count}")
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print(f"   Columns: {[col[1] for col in columns]}")
            
            # Show sample data if any exists
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                rows = cursor.fetchall()
                print(f"   Sample data:")
                for i, row in enumerate(rows, 1):
                    print(f"     {i}: {row}")
            else:
                print(f"   📭 No data in {table_name}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error reading database: {e}")

def create_test_user():
    """Create a test user in the database"""
    
    db_path = 'instance/stock_market.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create test user
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, email, created_at)
            VALUES (?, ?, ?)
        """, ('demo_trader', 'demo@trader.com', datetime.now().isoformat()))
        
        # Get the user ID
        cursor.execute("SELECT id FROM users WHERE username = ?", ('demo_trader',))
        user_result = cursor.fetchone()
        
        if user_result:
            user_id = user_result[0]
            print(f"✅ Test user created/found with ID: {user_id}")
            
            # Create bank account for user
            cursor.execute("""
                INSERT OR IGNORE INTO bank_accounts (user_id, balance, created_at)
                VALUES (?, ?, ?)
            """, (user_id, 10000.0, datetime.now().isoformat()))
            
            # Create sample portfolio
            sample_portfolio = [
                ('AAPL', 10, 145.50),
                ('GOOGL', 2, 2800.00),
                ('MSFT', 5, 300.25)
            ]
            
            for symbol, quantity, avg_price in sample_portfolio:
                cursor.execute("""
                    INSERT OR IGNORE INTO portfolio (user_id, stock_symbol, quantity, avg_price)
                    VALUES (?, ?, ?, ?)
                """, (user_id, symbol, quantity, avg_price))
            
            # Create sample trades
            sample_trades = [
                ('AAPL', 'buy', 10, 145.50, 1455.00),
                ('GOOGL', 'buy', 2, 2800.00, 5600.00),
                ('MSFT', 'buy', 5, 300.25, 1501.25)
            ]
            
            for symbol, trade_type, quantity, price, total in sample_trades:
                cursor.execute("""
                    INSERT OR IGNORE INTO trades 
                    (user_id, stock_symbol, trade_type, quantity, price, total_amount, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_id, symbol, trade_type, quantity, price, total, datetime.now().isoformat()))
            
            conn.commit()
            print(f"✅ Sample data created for user {user_id}")
            return user_id
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return None

if __name__ == "__main__":
    print("🔍 Checking Database...")
    check_database()
    
    print("\n" + "=" * 50)
    print("🆕 Creating Test User...")
    user_id = create_test_user()
    
    print("\n" + "=" * 50)
    print("🔍 Checking Database After Test Data...")
    check_database()