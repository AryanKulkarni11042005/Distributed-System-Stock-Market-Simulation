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
            },
            {
                'name': 'Analytics Service',
                'script': 'services/analytics_service/app.py',
                'port': 5005,
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
        
        required_dirs = ['utils', 'database', 'logs', 'spark_jobs', 'spark_results']
        for directory in required_dirs:
            if not os.path.exists(directory):
                logger.info(f"Creating missing directory: {directory}")
                os.makedirs(directory, exist_ok=True)
        
        init_files = [
            'utils/__init__.py',
            'database/__init__.py', 
            'services/__init__.py',
            'services/user_service/__init__.py',
            'services/bank_service/__init__.py',
            'services/stock_exchange_service/__init__.py', 
            'services/trade_logger_service/__init__.py',
            'services/analytics_service/__init__.py'
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
                if 'port' in service:
                    logger.info(f"Starting {service['name']} on port {service['port']}...")
                else:
                    logger.info(f"Starting {service['name']}...")
                
                process = subprocess.Popen([
                    sys.executable, service['script']
                ], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
                )
                
                proc_info = {
                    'name': service['name'],
                    'process': process,
                    'script': service['script']
                }
                if 'port' in service:
                    proc_info['port'] = service['port']

                self.processes.append(proc_info)
                
                time.sleep(service['startup_delay'])
                
                if process.poll() is None:
                    logger.info(f"✓ {service['name']} started successfully")
                else:
                    logger.error(f"✗ {service['name']} failed to start")
                    output, _ = process.communicate()
                    logger.error(f"Error output for {service['name']}:\n{output}")
                    
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
                    time.sleep(1)
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
            port_info = f"Port: {proc_info['port']:<6}" if 'port' in proc_info else "Port: N/A   "
            logger.info(f"{status_symbol} {proc_info['name']:<25} {port_info} Status: {status}")
        
        logger.info("="*70)
        logger.info("SERVICE ENDPOINTS:")
        logger.info("  - Time Server:         Pyro4://localhost:9090")
        logger.info("  - User Service:        http://localhost:5001")
        logger.info("  - Bank Service:        http://localhost:5002")
        logger.info("  - Stock Exchange:      http://localhost:5003")
        logger.info("  - Trade Logger:        http://localhost:5004")
        logger.info("  - Analytics Service:   http://localhost:5005")
        logger.info("="*70)
        logger.info("HEALTH CHECK URLS:")
        logger.info("  - User Service:        http://localhost:5001/health")
        logger.info("  - Bank Service:        http://localhost:5002/health")
        logger.info("  - Stock Exchange:      http://localhost:5003/health")
        logger.info("  - Trade Logger:        http://localhost:5004/health")
        logger.info("  - Analytics Service:   http://localhost:5005/health")
        logger.info("="*70)
    
    def monitor_services(self):
        """Monitor running services"""
        try:
            logger.info("Monitoring services... (Press Ctrl+C to stop)")
            while True:
                time.sleep(30)
                failed_services = [p['name'] for p in self.processes if p['process'].poll() is not None]
                if failed_services:
                    logger.warning(f"Failed services detected: {', '.join(failed_services)}")
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
                    self.processes = [p for p in self.processes if p['name'] != service['name']]
                    logger.info(f"Restarting {service['name']}...")
                    process = subprocess.Popen([sys.executable, service['script']], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    
                    proc_info = {'name': service['name'], 'process': process, 'script': service['script']}
                    if 'port' in service:
                        proc_info['port'] = service['port']
                    self.processes.append(proc_info)
                    
                    time.sleep(service['startup_delay'])
                    
                    if process.poll() is None:
                        logger.info(f"✓ {service['name']} restarted successfully")
                    else:
                        logger.error(f"✗ {service['name']} failed to restart")
                        
                except Exception as e:
                    logger.error(f"Error restarting {service['name']}: {e}")

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal")
    if 'orchestrator' in globals():
        orchestrator.stop_services()
    sys.exit(0)

def main():
    """Main function"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    global orchestrator
    orchestrator = ServiceOrchestrator()
    
    try:
        if orchestrator.start_services():
            logger.info("\n🚀 Stock Market Simulation started successfully!")
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
    main()
