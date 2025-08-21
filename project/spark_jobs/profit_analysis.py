from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import json
import os
import sys
from datetime import datetime

# Add path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class ProfitAnalyzer:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("StockMarketProfitAnalysis") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
        print("Profit Analyzer initialized")
    
    def analyze_user_profits(self):
        """Analyze profit/loss for each user"""
        try:
            # Read trades data
            csv_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'trades.csv')
            if os.path.exists(csv_path):
                trades_df = self.spark.read.option("header", "true").csv(csv_path)
            else:
                print(f"No trade data found at {csv_path}")
                return None
            
            if trades_df.count() == 0:
                print("No trade data found")
                return None
            
            # Convert data types
            trades_df = trades_df.withColumn("user_id", col("user_id").cast("integer")) \
                               .withColumn("quantity", col("quantity").cast("integer")) \
                               .withColumn("price", col("price").cast("double")) \
                               .withColumn("total_amount", col("total_amount").cast("double")) \
                               .withColumn("timestamp", to_timestamp(col("timestamp")))
            
            # Calculate user profits
            user_profits = trades_df.groupBy("user_id") \
                .agg(
                    sum(when(col("trade_type") == "buy", -col("total_amount"))
                        .when(col("trade_type") == "sell", col("total_amount"))).alias("net_profit"),
                    sum(when(col("trade_type") == "buy", col("total_amount"))).alias("total_invested"),
                    sum(when(col("trade_type") == "sell", col("total_amount"))).alias("total_sales"),
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
            
            # Convert to JSON
            profit_data = []
            for row in result:
                profit_data.append({
                    "user_id": row["user_id"],
                    "net_profit": float(row["net_profit"]) if row["net_profit"] else 0.0,
                    "total_invested": float(row["total_invested"]) if row["total_invested"] else 0.0,
                    "total_sales": float(row["total_sales"]) if row["total_sales"] else 0.0,
                    "profit_percentage": float(row["profit_percentage"]) if row["profit_percentage"] else 0.0,
                    "roi": float(row["roi"]) if row["roi"] else 0.0,
                    "total_trades": row["total_trades"],
                    "stocks_traded": row["stocks_traded"]
                })
            
            # Save results
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
    
    def analyze_stock_profitability(self):
        """Analyze which stocks generate most profits"""
        try:
            trades_df = self.spark.read.option("header", "true").csv("../logs/trades.csv")
            
            if trades_df.count() == 0:
                print("No trade data found")
                return None
            
            # Convert data types
            trades_df = trades_df.withColumn("quantity", col("quantity").cast("integer")) \
                               .withColumn("price", col("price").cast("double")) \
                               .withColumn("total_amount", col("total_amount").cast("double"))
            
            # Calculate stock profitability (for sellers)
            stock_profits = trades_df.groupBy("stock_symbol") \
                .agg(
                    sum(when(col("trade_type") == "sell", col("total_amount"))).alias("total_sales_value"),
                    sum(when(col("trade_type") == "buy", col("total_amount"))).alias("total_buy_value"),
                    avg(when(col("trade_type") == "sell", col("price"))).alias("avg_sell_price"),
                    avg(when(col("trade_type") == "buy", col("price"))).alias("avg_buy_price"),
                    sum(when(col("trade_type") == "sell", col("quantity"))).alias("total_sold"),
                    sum(when(col("trade_type") == "buy", col("quantity"))).alias("total_bought"),
                    count("*").alias("total_trades")
                ) \
                .withColumn("net_trading_value", 
                           coalesce(col("total_sales_value"), lit(0)) - coalesce(col("total_buy_value"), lit(0))) \
                .withColumn("price_appreciation",
                           when((col("avg_buy_price") > 0) & (col("avg_sell_price") > 0),
                                ((col("avg_sell_price") - col("avg_buy_price")) / col("avg_buy_price")) * 100)
                           .otherwise(0)) \
                .orderBy(desc("net_trading_value"))
            
            result = stock_profits.collect()
            
            # Convert to JSON
            stock_profit_data = []
            for row in result:
                stock_profit_data.append({
                    "stock_symbol": row["stock_symbol"],
                    "net_trading_value": float(row["net_trading_value"]) if row["net_trading_value"] else 0.0,
                    "total_sales_value": float(row["total_sales_value"]) if row["total_sales_value"] else 0.0,
                    "total_buy_value": float(row["total_buy_value"]) if row["total_buy_value"] else 0.0,
                    "avg_sell_price": float(row["avg_sell_price"]) if row["avg_sell_price"] else 0.0,
                    "avg_buy_price": float(row["avg_buy_price"]) if row["avg_buy_price"] else 0.0,
                    "price_appreciation": float(row["price_appreciation"]) if row["price_appreciation"] else 0.0,
                    "total_sold": int(row["total_sold"]) if row["total_sold"] else 0,
                    "total_bought": int(row["total_bought"]) if row["total_bought"] else 0,
                    "total_trades": row["total_trades"]
                })
            
            # Save results
            with open("spark_results/stock_profitability.json", "w") as f:
                json.dump({
                    "analysis_timestamp": datetime.now().isoformat(),
                    "stock_profitability": stock_profit_data
                }, f, indent=2)
            
            print(f"Stock profitability analysis completed. Analyzed {len(stock_profit_data)} stocks")
            return stock_profit_data
            
        except Exception as e:
            print(f"Error in stock profitability analysis: {e}")
            return None
    
    def analyze_profit_trends(self):
        """Analyze profit trends over time"""
        try:
            trades_df = self.spark.read.option("header", "true").csv("../logs/trades.csv")
            
            if trades_df.count() == 0:
                print("No trade data found")
                return None
            
            # Convert data types
            trades_df = trades_df.withColumn("total_amount", col("total_amount").cast("double")) \
                               .withColumn("timestamp", to_timestamp(col("timestamp")))
            
            # Calculate daily profit trends
            daily_profits = trades_df.groupBy(
                date_format(col("timestamp"), "yyyy-MM-dd").alias("date")
            ).agg(
                sum(when(col("trade_type") == "sell", col("total_amount"))).alias("daily_sales"),
                sum(when(col("trade_type") == "buy", col("total_amount"))).alias("daily_investments"),
                count(when(col("trade_type") == "sell", 1)).alias("sell_transactions"),
                count(when(col("trade_type") == "buy", 1)).alias("buy_transactions")
            ) \
            .withColumn("daily_net_flow", 
                       coalesce(col("daily_sales"), lit(0)) - coalesce(col("daily_investments"), lit(0))) \
            .orderBy("date")
            
            result = daily_profits.collect()
            
            # Convert to JSON
            profit_trends = []
            for row in result:
                profit_trends.append({
                    "date": row["date"],
                    "daily_sales": float(row["daily_sales"]) if row["daily_sales"] else 0.0,
                    "daily_investments": float(row["daily_investments"]) if row["daily_investments"] else 0.0,
                    "daily_net_flow": float(row["daily_net_flow"]) if row["daily_net_flow"] else 0.0,
                    "sell_transactions": row["sell_transactions"],
                    "buy_transactions": row["buy_transactions"]
                })
            
            # Save results
            with open("spark_results/profit_trends.json", "w") as f:
                json.dump({
                    "analysis_timestamp": datetime.now().isoformat(),
                    "profit_trends": profit_trends
                }, f, indent=2)
            
            print(f"Profit trends analysis completed. Analyzed {len(profit_trends)} days")
            return profit_trends
            
        except Exception as e:
            print(f"Error in profit trends analysis: {e}")
            return None
    
    def generate_profit_summary(self):
        """Generate overall profit summary"""
        try:
            trades_df = self.spark.read.option("header", "true").csv("../logs/trades.csv")
            
            if trades_df.count() == 0:
                print("No trade data found")
                return None
            
            # Convert data types
            trades_df = trades_df.withColumn("total_amount", col("total_amount").cast("double"))
            
            # Calculate overall summary
            summary = trades_df.agg(
                sum(when(col("trade_type") == "sell", col("total_amount"))).alias("total_sales"),
                sum(when(col("trade_type") == "buy", col("total_amount"))).alias("total_investments"),
                count(when(col("trade_type") == "sell", 1)).alias("total_sell_trades"),
                count(when(col("trade_type") == "buy", 1)).alias("total_buy_trades"),
                countDistinct("user_id").alias("total_traders"),
                countDistinct("stock_symbol").alias("total_stocks_traded")
            ).collect()[0]
            
            # Calculate summary metrics
            total_sales = float(summary["total_sales"]) if summary["total_sales"] else 0.0
            total_investments = float(summary["total_investments"]) if summary["total_investments"] else 0.0
            net_market_flow = total_sales - total_investments
            
            summary_data = {
                "total_sales": total_sales,
                "total_investments": total_investments,
                "net_market_flow": net_market_flow,
                "total_sell_trades": summary["total_sell_trades"],
                "total_buy_trades": summary["total_buy_trades"],
                "total_traders": summary["total_traders"],
                "total_stocks_traded": summary["total_stocks_traded"],
                "market_efficiency": (total_sales / total_investments * 100) if total_investments > 0 else 0
            }
            
            # Save results
            with open("spark_results/profit_summary.json", "w") as f:
                json.dump({
                    "analysis_timestamp": datetime.now().isoformat(),
                    "summary": summary_data
                }, f, indent=2)
            
            print("Profit summary generated successfully")
            return summary_data
            
        except Exception as e:
            print(f"Error generating profit summary: {e}")
            return None
    
    def close(self):
        """Close Spark session"""
        self.spark.stop()

def main():
    analyzer = ProfitAnalyzer()
    
    try:
        print("Starting Profit Analysis...")
        
        # Analyze user profits
        print("\n1. Analyzing user profits...")
        user_profits = analyzer.analyze_user_profits()
        
        # Analyze stock profitability
        print("\n2. Analyzing stock profitability...")
        stock_profits = analyzer.analyze_stock_profitability()
        
        # Analyze profit trends
        print("\n3. Analyzing profit trends...")
        profit_trends = analyzer.analyze_profit_trends()
        
        # Generate profit summary
        print("\n4. Generating profit summary...")
        profit_summary = analyzer.generate_profit_summary()
        
        print("\nProfit analysis completed successfully!")
        print("Results saved to:")
        print("  - spark_results/user_profits.json")
        print("  - spark_results/stock_profitability.json")
        print("  - spark_results/profit_trends.json")
        print("  - spark_results/profit_summary.json")
        
    except Exception as e:
        print(f"Profit analysis failed: {e}")
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()