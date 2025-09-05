from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, sum as spark_sum, avg, count, date_format, to_timestamp, lit, coalesce, desc
from pyspark.sql.types import *
import json
import os
import sys
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
import pandas as pd
import urllib.parse

# Add path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# --- MongoDB Configuration ---
MONGO_USER = os.getenv('MONGO_USER', 'aryankulkarni1104')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'Aryan@2005')
MONGO_CLUSTER = os.getenv('MONGO_CLUSTER', 'cluster0.qxaih.mongodb.net')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'stock_market_simulation')
encoded_password = urllib.parse.quote_plus(MONGO_PASSWORD)
MONGO_URI = f"mongodb+srv://{MONGO_USER}:{encoded_password}@{MONGO_CLUSTER}/{MONGO_DB_NAME}?retryWrites=true&w=majority"
# --- End MongoDB Configuration ---

class PortfolioAnalyzer:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("StockMarketPortfolioAnalysis") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
        print("Portfolio Analyzer initialized")

    def _get_trades_df_from_mongo(self):
        """Fetch trades data from MongoDB and convert to a Spark DataFrame."""
        try:
            client = MongoClient(MONGO_URI)
            db = client[MONGO_DB_NAME]
            trades_collection = db.trades
            
            trades_cursor = trades_collection.find({})
            trades_list = list(trades_cursor)
            client.close()

            if not trades_list:
                return None

            # Pre-process the list to handle MongoDB's BSON types
            processed_list = []
            for trade in trades_list:
                processed_trade = {}
                for key, value in trade.items():
                    if isinstance(value, ObjectId):
                        processed_trade[key] = str(value)
                    elif isinstance(value, datetime):
                        processed_trade[key] = value.isoformat()
                    else:
                        processed_trade[key] = value
                processed_list.append(processed_trade)

            if not processed_list:
                return None

            pandas_df = pd.DataFrame(processed_list)
            return self.spark.createDataFrame(pandas_df)
        except Exception as e:
            print(f"Error connecting to MongoDB or fetching data: {e}")
            return None

    def analyze_user_portfolio_growth(self, user_id=None):
        """Analyze portfolio growth over time for a specific user or all users"""
        try:
            trades_df = self._get_trades_df_from_mongo()
            if trades_df is None:
                print("No trade data found in MongoDB.")
                return None

            trades_df = trades_df.withColumn("user_id", col("user_id").cast("string")) \
                               .withColumn("quantity", col("quantity").cast("integer")) \
                               .withColumn("price", col("price").cast("double")) \
                               .withColumn("total_amount", col("total_amount").cast("double")) \
                               .withColumn("timestamp", to_timestamp(col("timestamp")))
            
            if user_id:
                trades_df = trades_df.filter(col("user_id") == user_id)
            
            portfolio_growth = trades_df.groupBy("user_id", "stock_symbol", 
                                               date_format(col("timestamp"), "yyyy-MM-dd").alias("date")) \
                .agg(
                    spark_sum(when(col("trade_type") == "buy", col("quantity"))
                        .when(col("trade_type") == "sell", -col("quantity"))).alias("net_quantity"),
                    avg("price").alias("avg_price"),
                    spark_sum("total_amount").alias("total_invested")
                ) \
                .filter(col("net_quantity") > 0)
            
            user_portfolio_value = portfolio_growth.groupBy("user_id", "date") \
                .agg(
                    spark_sum(col("net_quantity") * col("avg_price")).alias("portfolio_value"),
                    spark_sum("total_invested").alias("total_invested"),
                    count("stock_symbol").alias("stocks_held")
                ) \
                .withColumn("profit_loss", col("portfolio_value") - col("total_invested")) \
                .withColumn("profit_percentage", 
                           when(col("total_invested") > 0, 
                                (col("profit_loss") / col("total_invested")) * 100)
                           .otherwise(0)) \
                .orderBy("user_id", "date")
            
            portfolio_value_result = user_portfolio_value.collect()
            
            portfolio_data = [row.asDict() for row in portfolio_value_result]
            
            os.makedirs("spark_results", exist_ok=True)
            with open("spark_results/portfolio_analysis.json", "w") as f:
                json.dump({
                    "analysis_timestamp": datetime.now().isoformat(),
                    "user_filter": user_id,
                    "portfolio_growth": portfolio_data
                }, f, indent=2)
            
            print(f"Portfolio analysis completed. Found {len(portfolio_data)} portfolio snapshots")
            return portfolio_data
            
        except Exception as e:
            print(f"Error in portfolio analysis: {e}")
            return None
    
    def analyze_top_performers(self, limit=10):
        """Analyze top performing users by profit percentage"""
        try:
            trades_df = self._get_trades_df_from_mongo()
            if trades_df is None:
                print("No trade data found for top performers analysis.")
                return None

            trades_df = trades_df.withColumn("user_id", col("user_id").cast("string")) \
                               .withColumn("quantity", col("quantity").cast("integer")) \
                               .withColumn("price", col("price").cast("double")) \
                               .withColumn("total_amount", col("total_amount").cast("double"))
            
            user_performance = trades_df.groupBy("user_id") \
                .agg(
                    spark_sum(when(col("trade_type") == "buy", col("total_amount"))
                        .when(col("trade_type") == "sell", -col("total_amount"))).alias("net_investment"),
                    spark_sum(when(col("trade_type") == "sell", col("total_amount"))).alias("total_sales"),
                    count("*").alias("total_trades")
                ) \
                .withColumn("estimated_profit", 
                           coalesce(col("total_sales"), lit(0)) - abs(col("net_investment"))) \
                .withColumn("profit_percentage",
                           when(abs(col("net_investment")) > 0,
                                (col("estimated_profit") / abs(col("net_investment"))) * 100)
                           .otherwise(0)) \
                .orderBy(desc("profit_percentage")) \
                .limit(limit)
            
            result = user_performance.collect()
            
            top_performers = [row.asDict() for row in result]
            
            os.makedirs("spark_results", exist_ok=True)
            with open("spark_results/top_performers.json", "w") as f:
                json.dump({
                    "analysis_timestamp": datetime.now().isoformat(),
                    "top_performers": top_performers
                }, f, indent=2)
            
            print(f"Top performers analysis completed. Found {len(top_performers)} users")
            return top_performers
            
        except Exception as e:
            print(f"Error in top performers analysis: {e}")
            return None
    
    def close(self):
        """Close Spark session"""
        self.spark.stop()

def main():
    analyzer = PortfolioAnalyzer()
    
    try:
        print("Starting Portfolio Analysis...")
        print("\n1. Analyzing portfolio growth...")
        analyzer.analyze_user_portfolio_growth()
        
        print("\n2. Analyzing top performers...")
        analyzer.analyze_top_performers()
        
        print("\nPortfolio analysis completed successfully!")
        print("Results saved to:")
        print("  - spark_results/portfolio_analysis.json")
        print("  - spark_results/top_performers.json")
        
    except Exception as e:
        print(f"Portfolio analysis failed: {e}")
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()

