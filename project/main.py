import subprocess
import time
import sys
import signal
import os
import threading
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ServiceOrchestrator:
    """Orchestrates all services in the stock market simulation"""
    
    def __init__(self):
        self.processes = []
        # Fix the services list - remove time_server port and update paths
        self.services = [
            {
                'name': 'Time Server',
                'script': 'time_server/server.py',
                'startup_delay': 3
            },
            {
                'name': 'User Service', 
                'script': 'services/user_service/app.py',
                'port': 5001,
                'startup_delay': 2
            },
            {
                'name': 'Bank Service',
                'script': 'services/bank_service/app.py', 
                'port': 5002,
                'startup_delay': 2
            },
            {
                'name': 'Stock Exchange Service',
                'script': 'services/stock_exchange_service/app.py',
                'port': 5003,
                'startup_delay': 2
            },
            {
                'name': 'Trade Logger Service',
                'script': 'services/trade_logger_service/app.py',
                'port': 5004,
                'startup_delay': 2
            }
        ]
    
    def check_dependencies(self):
        """Check if all required files exist"""
        logger.info("Checking dependencies...")
        
        missing_files = []
        for service in self.services:
            script_path = service['script']
            if not os.path.exists(script_path):
                missing_files.append(script_path)
        
        # Check required directories
        required_dirs = ['utils', 'database', 'logs', 'spark_jobs', 'spark_results']
        for directory in required_dirs:
            if not os.path.exists(directory):
                logger.info(f"Creating missing directory: {directory}")
                os.makedirs(directory, exist_ok=True)
        
        # Create __init__.py files if missing
        init_files = [
            'utils/__init__.py',
            'database/__init__.py', 
            'services/__init__.py',
            'services/user_service/__init__.py',
            'services/bank_service/__init__.py',
            'services/stock_exchange_service/__init__.py', 
            'services/trade_logger_service/__init__.py'
        ]
        
        for init_file in init_files:
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write('# Python package marker\n')
                logger.info(f"Created {init_file}")
        
        if missing_files:
            logger.error(f"Missing required files: {missing_files}")
            return False
        
        logger.info("All dependencies found ✓")
        return True
    
    def start_services(self):
        """Start all services"""
        logger.info("Starting Stock Market Distributed Simulation...")
        logger.info("=" * 60)
        
        if not self.check_dependencies():
            logger.error("Dependency check failed. Exiting.")
            return False
        
        for service in self.services:
            try:
                logger.info(f"Starting {service['name']} on port {service['port']}...")
                
                # Start the service
                process = subprocess.Popen([
                    sys.executable, service['script']
                ], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
                )
                
                self.processes.append({
                    'name': service['name'],
                    'process': process,
                    'port': service['port'],
                    'script': service['script']
                })
                
                # Wait for service to start
                time.sleep(service['startup_delay'])
                
                # Check if process is still running
                if process.poll() is None:
                    logger.info(f"✓ {service['name']} started successfully")
                else:
                    logger.error(f"✗ {service['name']} failed to start")
                    
            except Exception as e:
                logger.error(f"Error starting {service['name']}: {e}")
        
        logger.info(f"\nStarted {len(self.processes)} services")
        self.print_service_status()
        return True
    
    def stop_services(self):
        """Stop all services"""
        logger.info("Stopping all services...")
        
        for proc_info in self.processes:
            try:
                if proc_info['process'].poll() is None:
                    proc_info['process'].terminate()
                    # Wait a bit for graceful shutdown
                    time.sleep(1)
                    
                    # Force kill if still running
                    if proc_info['process'].poll() is None:
                        proc_info['process'].kill()
                    
                    logger.info(f"✓ Stopped {proc_info['name']}")
                else:
                    logger.info(f"- {proc_info['name']} was already stopped")
            except Exception as e:
                logger.error(f"Error stopping {proc_info['name']}: {e}")
        
        self.processes.clear()
        logger.info("All services stopped")
    
    def print_service_status(self):
        """Print status of all services"""
        logger.info("\n" + "="*70)
        logger.info("STOCK MARKET SIMULATION - SERVICE STATUS")
        logger.info("="*70)
        
        for proc_info in self.processes:
            status = "RUNNING" if proc_info['process'].poll() is None else "STOPPED"
            status_symbol = "✓" if status == "RUNNING" else "✗"
            logger.info(f"{status_symbol} {proc_info['name']:<25} Port: {proc_info['port']:<6} Status: {status}")
        
        logger.info("="*70)
        logger.info("SERVICE ENDPOINTS:")
        logger.info("  - Time Server:         Pyro4://localhost:9090")
        logger.info("  - User Service:        http://localhost:5001")
        logger.info("  - Bank Service:        http://localhost:5002")
        logger.info("  - Stock Exchange:      http://localhost:5003")
        logger.info("  - Trade Logger:        http://localhost:5004")
        logger.info("="*70)
        logger.info("HEALTH CHECK URLS:")
        logger.info("  - User Service:        http://localhost:5001/health")
        logger.info("  - Bank Service:        http://localhost:5002/health")
        logger.info("  - Stock Exchange:      http://localhost:5003/health")
        logger.info("  - Trade Logger:        http://localhost:5004/health")
        logger.info("="*70)
        logger.info("API DOCUMENTATION:")
        logger.info("  - Get All Stocks:      GET  http://localhost:5003/stocks")
        logger.info("  - Create User:         POST http://localhost:5001/user/create")
        logger.info("  - Get Balance:         GET  http://localhost:5002/bank/balance/{user_id}")
        logger.info("  - Log Trade:           POST http://localhost:5004/trade/log")
        logger.info("="*70)
    
    def monitor_services(self):
        """Monitor running services"""
        try:
            logger.info("Monitoring services... (Press Ctrl+C to stop)")
            while True:
                time.sleep(30)  # Check every 30 seconds
                
                failed_services = []
                for proc_info in self.processes:
                    if proc_info['process'].poll() is not None:
                        failed_services.append(proc_info['name'])
                
                if failed_services:
                    logger.warning(f"Failed services detected: {', '.join(failed_services)}")
                    
                    # Attempt to restart failed services
                    self.restart_failed_services(failed_services)
                else:
                    logger.info("All services running normally")
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
    
    def restart_failed_services(self, failed_service_names):
        """Restart failed services"""
        logger.info(f"Attempting to restart failed services: {failed_service_names}")
        
        for service in self.services:
            if service['name'] in failed_service_names:
                try:
                    # Remove the failed process from our list
                    self.processes = [p for p in self.processes if p['name'] != service['name']]
                    
                    # Start the service again
                    logger.info(f"Restarting {service['name']}...")
                    process = subprocess.Popen([
                        sys.executable, service['script']
                    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    
                    self.processes.append({
                        'name': service['name'],
                        'process': process,
                        'port': service['port'],
                        'script': service['script']
                    })
                    
                    time.sleep(service['startup_delay'])
                    
                    if process.poll() is None:
                        logger.info(f"✓ {service['name']} restarted successfully")
                    else:
                        logger.error(f"✗ {service['name']} failed to restart")
                        
                except Exception as e:
                    logger.error(f"Error restarting {service['name']}: {e}")
    
    def run_analytics(self):
        """Run Spark analytics jobs"""
        logger.info("Running Spark Analytics...")
        
        analytics_jobs = [
            'spark_jobs/portfolio_analysis.py',
            'spark_jobs/volume_analysis.py', 
            'spark_jobs/profit_analysis.py'
        ]
        
        for job in analytics_jobs:
            if os.path.exists(job):
                try:
                    logger.info(f"Running {job}...")
                    result = subprocess.run([sys.executable, job], 
                                          capture_output=True, text=True, timeout=300)
                    if result.returncode == 0:
                        logger.info(f"✓ {job} completed successfully")
                    else:
                        logger.error(f"✗ {job} failed: {result.stderr}")
                except subprocess.TimeoutExpired:
                    logger.error(f"✗ {job} timed out")
                except Exception as e:
                    logger.error(f"✗ Error running {job}: {e}")
            else:
                logger.warning(f"Analytics job not found: {job}")

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal")
    if 'orchestrator' in globals():
        orchestrator.stop_services()
    sys.exit(0)

def main():
    """Main function"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    global orchestrator
    orchestrator = ServiceOrchestrator()
    
    try:
        # Start all services
        if orchestrator.start_services():
            logger.info("\n🚀 Stock Market Simulation started successfully!")
            logger.info("📊 All services are running and ready for trading")
            logger.info("⏰ Berkeley time synchronization is active")
            logger.info("💹 Stock prices are being simulated in real-time")
            logger.info("\n💡 You can now:")
            logger.info("   1. Create users and start trading")
            logger.info("   2. Monitor logs for synchronized timestamps")
            logger.info("   3. Run analytics: python spark_jobs/<analysis>.py")
            logger.info("   4. Check service health at /health endpoints")
            
            # Start monitoring
            orchestrator.monitor_services()
        else:
            logger.error("Failed to start services")
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        orchestrator.stop_services()
        logger.info("Stock Market Simulation stopped")

if __name__ == "__main__":
    print("🏦 Stock Market Distributed Simulation")
    print("🕐 Berkeley Algorithm Time Synchronization")
    print("🔄 Pyro4 RPC + REST API Services")
    print("⚡ Apache Spark Analytics")
    print("=" * 50)
    main()