import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from organizer import organize_file, load_config
from loguru import logger
import os

CONFIG = load_config()

class FileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            logger.info(f"Detected new file: {event.src_path}")
            organize_file(event.src_path, CONFIG['destination_directory'], CONFIG['file_types'])

if __name__ == "__main__":
    logger.info("Starting Local File Organizer Service...")
    event_handler = FileHandler()
    observer = Observer()
    observer.schedule(event_handler, CONFIG['source_directory'], recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Shutting down file organizer...")

    observer.join()
