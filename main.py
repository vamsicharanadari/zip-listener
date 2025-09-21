import os
import time
import shutil
import zipfile
import logging
import signal
import threading
from logging.handlers import RotatingFileHandler
from concurrent.futures import ThreadPoolExecutor

# -------------------
# Config from ENV
# -------------------
SOURCE_DIR = os.environ.get("SOURCE_DIR", "/app/source")
DEST_DIR = os.environ.get("DEST_DIR", "/app/destination")
RETRY_INTERVAL = int(os.environ.get("RETRY_INTERVAL", 5))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))
LOG_FILE = os.environ.get("LOG_FILE", "/app/logs/zip_listener.log")
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", 4))
SCAN_INTERVAL = int(os.environ.get("SCAN_INTERVAL", 10))  # seconds

# -------------------
# Logging
# -------------------
logger = logging.getLogger("ZipListener")
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=3)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# -------------------
# Helper functions
# -------------------
def is_file_ready(file_path):
    """Check if the file is fully copied and not locked."""
    try:
        with open(file_path, 'rb'):
            return True
    except Exception:
        return False

def delete_zip(zip_path):
    retries = 0
    while retries <= MAX_RETRIES:
        try:
            os.remove(zip_path)
            logger.info(f"Deleted zip: {zip_path}")
            return True
        except PermissionError:
            retries += 1
            logger.warning(f"Zip locked, retry {retries}/{MAX_RETRIES}: {zip_path}")
            time.sleep(RETRY_INTERVAL)
    logger.error(f"Failed to delete zip after retries: {zip_path}")
    return False

def extract_zip(zip_path):
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    target_dir = os.path.join(DEST_DIR, zip_name)
    os.makedirs(target_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
    except zipfile.BadZipFile:
        logger.error(f"Corrupted zip skipped: {zip_path}")
        shutil.rmtree(target_dir, ignore_errors=True)
        return False

    logger.info(f"Extracted '{zip_path}' to '{target_dir}'")
    return True

def process_zip(zip_path):
    logger.info(f"Processing zip: {zip_path}")
    # Wait until file is fully copied
    for _ in range(10):
        if is_file_ready(zip_path):
            break
        time.sleep(1)
    else:
        logger.warning(f"File not ready after waiting: {zip_path}")
        return

    if extract_zip(zip_path):
        delete_zip(zip_path)

def scan_for_zips(executor, processed_files):
    """Scan source folder for new .zip files"""
    for f in os.listdir(SOURCE_DIR):
        full_path = os.path.join(SOURCE_DIR, f)
        if os.path.isfile(full_path) and f.lower().endswith(".zip"):
            if full_path not in processed_files:
                executor.submit(process_zip, full_path)
                processed_files.add(full_path)

# -------------------
# Graceful shutdown
# -------------------
shutdown_event = threading.Event()
def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown_event.set()
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# -------------------
# Main
# -------------------
if __name__ == "__main__":
    os.makedirs(SOURCE_DIR, exist_ok=True)
    os.makedirs(DEST_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    processed_files = set()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        logger.info(f"Started periodic scanning of {SOURCE_DIR} every {SCAN_INTERVAL}s with {MAX_WORKERS} workers")
        try:
            while not shutdown_event.is_set():
                scan_for_zips(executor, processed_files)
                time.sleep(SCAN_INTERVAL)
        finally:
            logger.info("Shutting down, waiting for ongoing zip tasks to finish...")
            executor.shutdown(wait=True)
            logger.info("All tasks completed. Exiting.")