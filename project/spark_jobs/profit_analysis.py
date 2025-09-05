from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, sum as spark_sum, avg, count, date_format, to_timestamp, lit, coalesce, desc, countDistinct
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

class ProfitAnalyzer:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("StockMarketProfitAnalysis") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
        print("Profit Analyzer initialized")

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

    def analyze_user_profits(self):
        """Analyze profit/loss for each user"""
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
            
            user_profits = trades_df.groupBy("user_id") \
                .agg(
                    spark_sum(when(col("trade_type") == "buy", -col("total_amount"))
                        .when(col("trade_type") == "sell", col("total_amount"))).alias("net_profit"),
                    spark_sum(when(col("trade_type") == "buy", col("total_amount"))).alias("total_invested"),
                    spark_sum(when(col("trade_type") == "sell", col("total_amount"))).alias("total_sales"),
                    count("*").alias("total_trades"),
                    countDistinct("stock_symbol").alias("stocks_traded")
                ) \
                .withColumn("profit_percentage",
                           when(col("total_invested") > 0,
                                (col("net_profit") / col("total_invested")) * 100)
                           .otherwise(0)) \
                .withColumn("roi", col("profit_percentage")) \
                .orderBy(desc("net_profit"))
            
            result = user_profits.collect()
            
            profit_data = [row.asDict() for row in result]
            
            os.makedirs("spark_results", exist_ok=True)
            with open("spark_results/user_profits.json", "w") as f:
                json.dump({
                    "analysis_timestamp": datetime.now().isoformat(),
                    "user_profits": profit_data
                }, f, indent=2)
            
            print(f"User profit analysis completed. Analyzed {len(profit_data)} users")
            return profit_data
            
        except Exception as e:
            print(f"Error in user profit analysis: {e}")
            return None
    
    def close(self):
        """Close Spark session"""
        self.spark.stop()

def main():
    analyzer = ProfitAnalyzer()
    
    try:
        print("Starting Profit Analysis...")
        print("\n1. Analyzing user profits...")
        analyzer.analyze_user_profits()
        
        print("\nProfit analysis completed successfully!")
        print("Results saved to: spark_results/user_profits.json")
        
    except Exception as e:
        print(f"Profit analysis failed: {e}")
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()

