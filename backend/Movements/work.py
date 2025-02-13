import threading
import time
import logging

logger = logging.getLogger(__name__)

def worker(stop_event: threading.Event):
    try:
        while not stop_event.is_set():
            # logger.info("Working...")
            time.sleep(10)
    except Exception as e:
        logger.error(f"Error in work: {str(e)}")
    finally:
        logger.info("Work activity stopped gracefully")