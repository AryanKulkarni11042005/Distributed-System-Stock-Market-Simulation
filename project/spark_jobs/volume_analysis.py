from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, sum as spark_sum, avg, count, date_format, to_timestamp, min as spark_min, max as spark_max, desc, countDistinct
from pyspark.sql.types import *
import json
import os
import sys
from datetime import datetime
from pymongo import MongoClient
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

class VolumeAnalyzer:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("StockMarketVolumeAnalysis") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
        print("Volume Analyzer initialized")

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

            pandas_df = pd.DataFrame(trades_list)
            if '_id' in pandas_df.columns:
                pandas_df['_id'] = pandas_df['_id'].astype(str)

            return self.spark.createDataFrame(pandas_df)
        except Exception as e:
            print(f"Error connecting to MongoDB or fetching data: {e}")
            return None

    def analyze_trading_volume_by_stock(self):
        """Analyze trading volume for each stock"""
        try:
            trades_df = self._get_trades_df_from_mongo()
            if trades_df is None:
                print("No trade data found in MongoDB.")
                return None

            trades_df = trades_df.withColumn("quantity", col("quantity").cast("integer")) \
                               .withColumn("price", col("price").cast("double")) \
                               .withColumn("total_amount", col("total_amount").cast("double")) \
                               .withColumn("timestamp", to_timestamp(col("timestamp")))
            
            volume_by_stock = trades_df.groupBy("stock_symbol") \
                .agg(
                    spark_sum("quantity").alias("total_volume"),
                    spark_sum("total_amount").alias("total_value"),
                    count("*").alias("total_trades"),
                    avg("price").alias("avg_price"),
                    spark_min("price").alias("min_price"),
                    spark_max("price").alias("max_price"),
                    spark_sum(when(col("trade_type") == "buy", col("quantity"))).alias("buy_volume"),
                    spark_sum(when(col("trade_type") == "sell", col("quantity"))).alias("sell_volume")
                ) \
                .withColumn("price_volatility", col("max_price") - col("min_price")) \
                .withColumn("buy_sell_ratio", 
                           when(col("sell_volume") > 0, col("buy_volume") / col("sell_volume"))
                           .otherwise(float('inf'))) \
                .orderBy(desc("total_volume"))
            
            result = volume_by_stock.collect()
            
            volume_data = [row.asDict() for row in result]
            
            os.makedirs("spark_results", exist_ok=True)
            with open("spark_results/volume_analysis.json", "w") as f:
                json.dump({
                    "analysis_timestamp": datetime.now().isoformat(),
                    "volume_by_stock": volume_data
                }, f, indent=2)
            
            print(f"Volume analysis completed. Analyzed {len(volume_data)} stocks")
            return volume_data
            
        except Exception as e:
            print(f"Error in volume analysis: {e}")
            return None
    
    def analyze_daily_trading_volume(self):
        """Analyze daily trading volume trends"""
        try:
            trades_df = self._get_trades_df_from_mongo()
            if trades_df is None:
                print("No trade data for daily analysis.")
                return None

            trades_df = trades_df.withColumn("quantity", col("quantity").cast("integer")) \
                               .withColumn("total_amount", col("total_amount").cast("double")) \
                               .withColumn("timestamp", to_timestamp(col("timestamp")))
            
            daily_volume = trades_df.groupBy(
                date_format(col("timestamp"), "yyyy-MM-dd").alias("date")
            ).agg(
                spark_sum("quantity").alias("total_daily_volume"),
                spark_sum("total_amount").alias("total_daily_value"),
                count("*").alias("total_daily_trades"),
                countDistinct("stock_symbol").alias("stocks_traded"),
                countDistinct("user_id").alias("active_users")
            ).orderBy("date")
            
            result = daily_volume.collect()
            
            daily_data = [row.asDict() for row in result]
            
            with open("spark_results/daily_volume_analysis.json", "w") as f:
                json.dump({
                    "analysis_timestamp": datetime.now().isoformat(),
                    "daily_volume": daily_data
                }, f, indent=2)
            
            print(f"Daily volume analysis completed. Analyzed {len(daily_data)} days")
            return daily_data
            
        except Exception as e:
            print(f"Error in daily volume analysis: {e}")
            return None
    
    def close(self):
        """Close Spark session"""
        self.spark.stop()

def main():
    analyzer = VolumeAnalyzer()
    
    try:
        print("Starting Volume Analysis...")
        print("\n1. Analyzing trading volume by stock...")
        analyzer.analyze_trading_volume_by_stock()
        
        print("\n2. Analyzing daily trading volume...")
        analyzer.analyze_daily_trading_volume()
        
        print("\nVolume analysis completed successfully!")
        print("Results saved to:")
        print("  - spark_results/volume_analysis.json")
        print("  - spark_results/daily_volume_analysis.json")
        
    except Exception as e:
        print(f"Volume analysis failed: {e}")
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()
