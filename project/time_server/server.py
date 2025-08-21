import Pyro4
import threading
import time
import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

# Add path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.logger import setup_logger

logger = setup_logger(__name__)

@Pyro4.expose
class TimeServer:
    """
    Berkeley Algorithm Implementation
    - Collects timestamps from all registered services
    - Computes average offset
    - Provides synchronized time to services
    """
    
    def __init__(self):
        self.master_time = datetime.utcnow()
        self.service_times = defaultdict(lambda: {'last_sync': None, 'offset': 0})
        self.lock = threading.Lock()
        self.sync_interval = 30  # seconds
        
        # Start background synchronization thread
        self.sync_thread = threading.Thread(target=self._background_sync, daemon=True)
        self.sync_thread.start()
        
        logger.info("Time Server initialized with Berkeley Algorithm")
    
    def register_service(self, service_id):
        """Register a service for time synchronization"""
        with self.lock:
            self.service_times[service_id] = {
                'last_sync': datetime.utcnow(),
                'offset': 0
            }
        logger.info(f"Registered service: {service_id}")
        return True
    
    def report_time(self, service_id, local_time_str):
        """Service reports its local time for synchronization"""
        try:
            local_time = datetime.fromisoformat(local_time_str.replace('Z', '+00:00'))
            current_time = datetime.utcnow()
            
            with self.lock:
                # Calculate the offset between service time and master time
                offset = (current_time - local_time).total_seconds()
                self.service_times[service_id]['last_sync'] = current_time
                self.service_times[service_id]['offset'] = offset
            
            logger.info(f"Service {service_id} reported time, offset: {offset:.3f}s")
            return True
            
        except Exception as e:
            logger.error(f"Error processing time report from {service_id}: {e}")
            return False
    
    def get_synchronized_time(self, service_id):
        """Get synchronized time for a service"""
        with self.lock:
            # Use Berkeley algorithm: adjust based on computed average offset
            current_time = datetime.utcnow()
            
            # If service is not registered, register it
            if service_id not in self.service_times:
                self.register_service(service_id)
            
            # Apply the computed offset
            service_offset = self.service_times[service_id]['offset']
            synchronized_time = current_time - timedelta(seconds=service_offset)
            
            return synchronized_time.isoformat()
    
    def _background_sync(self):
        """Background thread for periodic synchronization"""
        while True:
            try:
                time.sleep(self.sync_interval)
                self._perform_berkeley_sync()
            except Exception as e:
                logger.error(f"Error in background sync: {e}")
    
    def _perform_berkeley_sync(self):
        """Perform Berkeley algorithm synchronization"""
        with self.lock:
            if not self.service_times:
                return
            
            # Collect all offsets from services that have reported recently
            recent_offsets = []
            current_time = datetime.utcnow()
            
            for service_id, data in self.service_times.items():
                if data['last_sync'] and (current_time - data['last_sync']).seconds < 60:
                    recent_offsets.append(data['offset'])
            
            if recent_offsets:
                # Calculate average offset (Berkeley algorithm)
                avg_offset = statistics.mean(recent_offsets)
                
                # Adjust master time based on average offset
                self.master_time = current_time - timedelta(seconds=avg_offset)
                
                logger.info(f"Berkeley sync completed. Average offset: {avg_offset:.3f}s, Services: {len(recent_offsets)}")
    
    def get_server_stats(self):
        """Get time server statistics"""
        with self.lock:
            stats = {
                'master_time': self.master_time.isoformat(),
                'registered_services': len(self.service_times),
                'services': {}
            }
            
            for service_id, data in self.service_times.items():
                stats['services'][service_id] = {
                    'last_sync': data['last_sync'].isoformat() if data['last_sync'] else None,
                    'offset': data['offset']
                }
            
            return stats

def start_time_server():
    """Start the Pyro4 time server"""
    daemon = Pyro4.Daemon(host='localhost', port=9090)
    time_server = TimeServer()
    uri = daemon.register(time_server, "timeserver")
    
    logger.info(f"Time Server ready. URI: {uri}")
    logger.info("Time Server listening on localhost:9090")
    
    daemon.requestLoop()

if __name__ == "__main__":
    start_time_server()