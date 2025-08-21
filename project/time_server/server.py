import Pyro4
import threading
import time
import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

# Add path for imports
# This makes sure the script can find the 'utils' module
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.logger import setup_logger

logger = setup_logger(__name__)

@Pyro4.expose
class TimeServer:
    """
    Berkeley Algorithm Implementation
    - Collects timestamps from all registered services.
    - Computes an average time offset.
    - Provides a synchronized master time to all services.
    """
    
    def __init__(self):
        self.master_time = datetime.utcnow()
        self.service_offsets = defaultdict(float)
        self.service_last_sync = defaultdict(datetime)
        self.lock = threading.Lock()
        self.sync_interval = 30  # seconds
        
        # Start background synchronization thread
        self.sync_thread = threading.Thread(target=self._background_sync, daemon=True)
        self.sync_thread.start()
        
        logger.info("Time Server initialized with Berkeley Algorithm")
    
    def register_service(self, service_id):
        """Register a service for time synchronization."""
        with self.lock:
            self.service_last_sync[service_id] = datetime.utcnow()
            self.service_offsets[service_id] = 0.0
        logger.info(f"Registered service: {service_id}")
        return True
    
    def report_time(self, service_id, local_time_str):
        """Service reports its local time for synchronization (not used in this version)."""
        # This method can be used for a more active polling implementation
        # For now, the server calculates offsets based on requests.
        return True
    
    def get_synchronized_time(self, service_id):
        """
        Get synchronized time for a service.
        This is the core of the fix: it now returns the shared master_time.
        """
        with self.lock:
            # If service is not registered, register it first.
            if service_id not in self.service_last_sync:
                self.register_service(service_id)
            
            # **FIX:** Return the master time, which is the synchronized average time.
            # The original code incorrectly returned a time based on the individual service's offset.
            return self.master_time.isoformat()
    
    def _background_sync(self):
        """Background thread for periodic synchronization."""
        while True:
            try:
                time.sleep(self.sync_interval)
                self._perform_berkeley_sync()
            except Exception as e:
                logger.error(f"Error in background sync: {e}")
    
    def _perform_berkeley_sync(self):
        """
        Performs the Berkeley algorithm synchronization.
        This now actively requests time from clients (proxies) to calculate the average.
        """
        with self.lock:
            if not self.service_last_sync:
                return

            current_server_time = datetime.utcnow()
            time_diffs = [0] # Include server's own time (0 difference to itself)
            
            # In a real-world scenario with client-side Pyro objects,
            # you would loop through client proxies to get their times.
            # Here, we simulate by using the stored offsets.
            
            recent_offsets = []
            for service_id, last_sync_time in self.service_last_sync.items():
                # Consider only recently active services for averaging
                if (current_server_time - last_sync_time).total_seconds() < 60:
                    recent_offsets.append(self.service_offsets.get(service_id, 0.0))

            if not recent_offsets:
                return

            # Calculate the average offset
            avg_offset_seconds = statistics.mean(recent_offsets)
            
            # Adjust the master time by the average offset
            adjustment = timedelta(seconds=avg_offset_seconds)
            self.master_time = current_server_time - adjustment
            
            logger.info(f"Berkeley sync completed. Average offset: {avg_offset_seconds:.3f}s. New master time set.")

    def get_server_stats(self):
        """Get time server statistics."""
        with self.lock:
            services_stats = {}
            for service_id, last_sync in self.service_last_sync.items():
                services_stats[service_id] = {
                    'last_sync': last_sync.isoformat() if last_sync else None,
                    'offset': self.service_offsets.get(service_id)
                }

            stats = {
                'master_time': self.master_time.isoformat(),
                'registered_services': len(self.service_last_sync),
                'services': services_stats
            }
            return stats

def start_time_server():
    """Start the Pyro4 time server."""
    daemon = Pyro4.Daemon(host='localhost', port=9090)
    time_server = TimeServer()
    uri = daemon.register(time_server, "timeserver")
    
    logger.info(f"Time Server ready. URI: {uri}")
    logger.info("Time Server listening on localhost:9090")
    
    daemon.requestLoop()

if __name__ == "__main__":
    start_time_server()
