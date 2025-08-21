from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import json
import os
import sys
from datetime import datetime

# Add path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class VolumeAnalyzer:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("StockMarketVolumeAnalysis") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
        print("Volume Analyzer initialized")
    
    def analyze_trading_volume_by_stock(self):
        """Analyze trading volume for each stock"""
        try:
            # Read trades data
            csv_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'trades.csv')
            if os.path.exists(csv_path):
                trades_df = self.spark.read.option("header", "true").csv(csv_path)
            else:
                print(f"No trade data found at {csv_path}")
                return None
            
            # Convert data types
            trades_df = trades_df.withColumn("quantity", col("quantity").cast("integer")) \
                               .withColumn("price", col("price").cast("double")) \
                               .withColumn("total_amount", col("total_amount").cast("double")) \
                               .withColumn("timestamp", to_timestamp(col("timestamp")))
            
            # Calculate volume metrics by stock
            volume_by_stock = trades_df.groupBy("stock_symbol") \
                .agg(
                    sum("quantity").alias("total_volume"),
                    sum("total_amount").alias("total_value"),
                    count("*").alias("total_trades"),
                    avg("price").alias("avg_price"),
                    min("price").alias("min_price"),
                    max("price").alias("max_price"),
                    sum(when(col("trade_type") == "buy", col("quantity"))).alias("buy_volume"),
                    sum(when(col("trade_type") == "sell", col("quantity"))).alias("sell_volume")
                ) \
                .withColumn("price_volatility", col("max_price") - col("min_price")) \
                .withColumn("buy_sell_ratio", 
                           when(col("sell_volume") > 0, col("buy_volume") / col("sell_volume"))
                           .otherwise(float('inf'))) \
                .orderBy(desc("total_volume"))
            
            result = volume_by_stock.collect()
            
            # Convert to JSON
            volume_data = []
            for row in result:
                volume_data.append({
                    "stock_symbol": row["stock_symbol"],
                    "total_volume": int(row["total_volume"]) if row["total_volume"] else 0,
                    "total_value": float(row["total_value"]) if row["total_value"] else 0.0,
                    "total_trades": row["total_trades"],
                    "avg_price": float(row["avg_price"]) if row["avg_price"] else 0.0,
                    "min_price": float(row["min_price"]) if row["min_price"] else 0.0,
                    "max_price": float(row["max_price"]) if row["max_price"] else 0.0,
                    "price_volatility": float(row["price_volatility"]) if row["price_volatility"] else 0.0,
                    "buy_volume": int(row["buy_volume"]) if row["buy_volume"] else 0,
                    "sell_volume": int(row["sell_volume"]) if row["sell_volume"] else 0,
                    "buy_sell_ratio": float(row["buy_sell_ratio"]) if row["buy_sell_ratio"] != float('inf') else None
                })
            
            # Save results
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
            trades_df = self.spark.read.option("header", "true").csv("logs/trades.csv")
            
            if trades_df.count() == 0:
                print("No trade data found")
                return None
            
            # Convert data types
            trades_df = trades_df.withColumn("quantity", col("quantity").cast("integer")) \
                               .withColumn("total_amount", col("total_amount").cast("double")) \
                               .withColumn("timestamp", to_timestamp(col("timestamp")))
            
            # Calculate daily volume
            daily_volume = trades_df.groupBy(
                date_format(col("timestamp"), "yyyy-MM-dd").alias("date")
            ).agg(
                sum("quantity").alias("total_daily_volume"),
                sum("total_amount").alias("total_daily_value"),
                count("*").alias("total_daily_trades"),
                countDistinct("stock_symbol").alias("stocks_traded"),
                countDistinct("user_id").alias("active_users")
            ).orderBy("date")
            
            result = daily_volume.collect()
            
            # Convert to JSON
            daily_data = []
            for row in result:
                daily_data.append({
                    "date": row["date"],
                    "total_daily_volume": int(row["total_daily_volume"]) if row["total_daily_volume"] else 0,
                    "total_daily_value": float(row["total_daily_value"]) if row["total_daily_value"] else 0.0,
                    "total_daily_trades": row["total_daily_trades"],
                    "stocks_traded": row["stocks_traded"],
                    "active_users": row["active_users"]
                })
            
            # Save results
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
    
    def analyze_most_traded_stocks(self, limit=10):
        """Find most traded stocks by volume and value"""
        try:
            trades_df = self.spark.read.option("header", "true").csv("logs/trades.csv")
            
            if trades_df.count() == 0:
                print("No trade data found")
                return None
            
            # Convert data types
            trades_df = trades_df.withColumn("quantity", col("quantity").cast("integer")) \
                               .withColumn("total_amount", col("total_amount").cast("double"))
            
            # Most traded by volume
            most_traded_volume = trades_df.groupBy("stock_symbol") \
                .agg(sum("quantity").alias("total_volume")) \
                .orderBy(desc("total_volume")) \
                .limit(limit)
            
            # Most traded by value
            most_traded_value = trades_df.groupBy("stock_symbol") \
                .agg(sum("total_amount").alias("total_value")) \
                .orderBy(desc("total_value")) \
                .limit(limit)
            
            volume_result = most_traded_volume.collect()
            value_result = most_traded_value.collect()
            
            # Convert to JSON
            most_traded_data = {
                "by_volume": [
                    {
                        "stock_symbol": row["stock_symbol"],
                        "total_volume": int(row["total_volume"])
                    } for row in volume_result
                ],
                "by_value": [
                    {
                        "stock_symbol": row["stock_symbol"],
                        "total_value": float(row["total_value"])
                    } for row in value_result
                ]
            }
            
            # Save results
            with open("spark_results/most_traded_stocks.json", "w") as f:
                json.dump({
                    "analysis_timestamp": datetime.now().isoformat(),
                    "most_traded": most_traded_data
                }, f, indent=2)
            
            print(f"Most traded stocks analysis completed")
            return most_traded_data
            
        except Exception as e:
            print(f"Error in most traded analysis: {e}")
            return None
    
    def close(self):
        """Close Spark session"""
        self.spark.stop()

def main():
    analyzer = VolumeAnalyzer()
    
    try:
        print("Starting Volume Analysis...")
        
        # Analyze trading volume by stock
        print("\n1. Analyzing trading volume by stock...")
        volume_by_stock = analyzer.analyze_trading_volume_by_stock()
        
        # Analyze daily trading volume
        print("\n2. Analyzing daily trading volume...")
        daily_volume = analyzer.analyze_daily_trading_volume()
        
        # Find most traded stocks
        print("\n3. Finding most traded stocks...")
        most_traded = analyzer.analyze_most_traded_stocks()
        
        print("\nVolume analysis completed successfully!")
        print("Results saved to:")
        print("  - spark_results/volume_analysis.json")
        print("  - spark_results/daily_volume_analysis.json")
        print("  - spark_results/most_traded_stocks.json")
        
    except Exception as e:
        print(f"Volume analysis failed: {e}")
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()