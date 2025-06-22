import os
import sys
import signal
import time
from pathlib import Path
from loguru import logger
from prometheus_client import Counter, Histogram, start_http_server
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from etl import extract_data, save_output, load_config

# Metrics
FILES_PROCESSED = Counter('files_processed_total', 'Total files processed', ['status'])
PROCESSING_TIME = Histogram('file_processing_seconds', 'Time spent processing files')

class DocETLHandler(FileSystemEventHandler):
    def __init__(self, config):
        self.config = config
        self.processing = set()

    def on_created(self, event):
        if not event.is_directory and event.src_path not in self.processing:
            self.process_file(event.src_path)

    @PROCESSING_TIME.time()
    def process_file(self, file_path):
        self.processing.add(file_path)
        try:
            logger.info(f"Processing: {file_path}")
            
            content = extract_data(file_path)
            if content:
                file_name = Path(file_path).stem
                output_file = f"{file_name}.txt"
                output_path = os.path.join(self.config['output_directory'], output_file)
                save_output(output_path, content)
                FILES_PROCESSED.labels(status='success').inc()
                logger.info(f"Successfully processed: {file_path}")
            else:
                logger.warning(f"No content extracted from: {file_path}")
                FILES_PROCESSED.labels(status='no_content').inc()
                
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            FILES_PROCESSED.labels(status='error').inc()
        finally:
            self.processing.discard(file_path)

def setup_logging():
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=os.getenv("LOG_LEVEL", "INFO")
    )
    logger.add(
        "logs/docetl.log",
        rotation="10 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="INFO"
    )

def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

def main():
    setup_logging()
    
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start metrics server
    start_http_server(8000)
    logger.info("Metrics server started on port 8000")
    
    config = load_config()
    input_dir = config['input_directory']
    output_dir = config['output_directory']

    # Create directories
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # Validate directories
    if not os.path.exists(input_dir):
        logger.error(f"Input directory '{input_dir}' does not exist")
        sys.exit(1)

    # Process existing files
    handler = DocETLHandler(config)
    try:
        existing_files = [f for f in os.listdir(input_dir) 
                         if os.path.isfile(os.path.join(input_dir, f))]
        
        for file_name in existing_files:
            file_path = os.path.join(input_dir, file_name)
            handler.process_file(file_path)
            
    except Exception as e:
        logger.error(f"Error processing existing files: {e}")

    # Set up file watcher
    logger.info(f"Starting DocETL service, watching: {input_dir}")
    observer = Observer()
    observer.schedule(handler, input_dir, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        observer.stop()
        observer.join()
        logger.info("DocETL service stopped")

if __name__ == "__main__":
    main()