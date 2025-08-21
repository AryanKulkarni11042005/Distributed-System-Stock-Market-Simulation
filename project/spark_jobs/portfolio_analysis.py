from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import json
import os
import sys
from datetime import datetime

# Add path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class PortfolioAnalyzer:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("StockMarketPortfolioAnalysis") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
        print("Portfolio Analyzer initialized")
    
    def analyze_user_portfolio_growth(self, user_id=None):
        """Analyze portfolio growth over time for a specific user or all users"""
        try:
            # Read trades data
            csv_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'trades.csv')
            if os.path.exists(csv_path):
                trades_df = self.spark.read.option("header", "true").csv(csv_path)
            else:
                print(f"No trade data found at {csv_path}")
                return None
            
            # Convert data types
            trades_df = trades_df.withColumn("user_id", col("user_id").cast("integer")) \
                               .withColumn("quantity", col("quantity").cast("integer")) \
                               .withColumn("price", col("price").cast("double")) \
                               .withColumn("total_amount", col("total_amount").cast("double")) \
                               .withColumn("timestamp", to_timestamp(col("timestamp")))
            
            # Filter by user if specified
            if user_id:
                trades_df = trades_df.filter(col("user_id") == user_id)
            
            # Calculate portfolio value over time
            portfolio_growth = trades_df.groupBy("user_id", "stock_symbol", 
                                               date_format(col("timestamp"), "yyyy-MM-dd").alias("date")) \
                .agg(
                    sum(when(col("trade_type") == "buy", col("quantity"))
                        .when(col("trade_type") == "sell", -col("quantity"))).alias("net_quantity"),
                    avg("price").alias("avg_price"),
                    sum("total_amount").alias("total_invested")
                ) \
                .filter(col("net_quantity") > 0)  # Only consider positions held
            
            # Calculate portfolio value per user per day
            user_portfolio_value = portfolio_growth.groupBy("user_id", "date") \
                .agg(
                    sum(col("net_quantity") * col("avg_price")).alias("portfolio_value"),
                    sum("total_invested").alias("total_invested"),
                    count("stock_symbol").alias("stocks_held")
                ) \
                .withColumn("profit_loss", col("portfolio_value") - col("total_invested")) \
                .withColumn("profit_percentage", 
                           when(col("total_invested") > 0, 
                                (col("profit_loss") / col("total_invested")) * 100)
                           .otherwise(0)) \
                .orderBy("user_id", "date")
            
            # Save results
            result = portfolio_growth.collect()
            portfolio_value_result = user_portfolio_value.collect()
            
            # Convert to JSON for frontend
            portfolio_data = []
            for row in portfolio_value_result:
                portfolio_data.append({
                    "user_id": row["user_id"],
                    "date": row["date"],
                    "portfolio_value": float(row["portfolio_value"]) if row["portfolio_value"] else 0.0,
                    "total_invested": float(row["total_invested"]) if row["total_invested"] else 0.0,
                    "profit_loss": float(row["profit_loss"]) if row["profit_loss"] else 0.0,
                    "profit_percentage": float(row["profit_percentage"]) if row["profit_percentage"] else 0.0,
                    "stocks_held": row["stocks_held"]
                })
            
            # Save to JSON file
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
            trades_df = self.spark.read.option("header", "true").csv("logs/trades.csv")
            
            if trades_df.count() == 0:
                print("No trade data found")
                return None
            
            # Convert data types
            trades_df = trades_df.withColumn("user_id", col("user_id").cast("integer")) \
                               .withColumn("quantity", col("quantity").cast("integer")) \
                               .withColumn("price", col("price").cast("double")) \
                               .withColumn("total_amount", col("total_amount").cast("double"))
            
            # Calculate user performance
            user_performance = trades_df.groupBy("user_id") \
                .agg(
                    sum(when(col("trade_type") == "buy", col("total_amount"))
                        .when(col("trade_type") == "sell", -col("total_amount"))).alias("net_investment"),
                    sum(when(col("trade_type") == "sell", col("total_amount"))).alias("total_sales"),
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
            
            # Convert to JSON
            top_performers = []
            for row in result:
                top_performers.append({
                    "user_id": row["user_id"],
                    "net_investment": float(row["net_investment"]) if row["net_investment"] else 0.0,
                    "total_sales": float(row["total_sales"]) if row["total_sales"] else 0.0,
                    "estimated_profit": float(row["estimated_profit"]) if row["estimated_profit"] else 0.0,
                    "profit_percentage": float(row["profit_percentage"]) if row["profit_percentage"] else 0.0,
                    "total_trades": row["total_trades"]
                })
            
            # Save results
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
        
        # Analyze overall portfolio growth
        print("\n1. Analyzing portfolio growth...")
        portfolio_growth = analyzer.analyze_user_portfolio_growth()
        
        # Analyze top performers
        print("\n2. Analyzing top performers...")
        top_performers = analyzer.analyze_top_performers()
        
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