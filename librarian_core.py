# ==========================================================
# DCI Librarian Core - Main Engine Skeleton
# Developed by DCI Veridictum Lab (2026)
# Author: Dariusz - DCI Architect
# License: GNU GPL v3.0
# All rights reserved. Visionary non-commercial module.
# ==========================================================

import os
import time
import json
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- Configuration ---
LM_STUDIO_API = "http://localhost:1234"
HEADERS = {"Content-Type": "application/json"}
WORKSPACE_PATH = os.path.expanduser('~/VSCodeWorkspace')

class LibrarianHandler(FileSystemEventHandler):
    """
    DCI Librarian Handler: 
    Monitors workspace changes and synchronizes context with LM Studio.
    """
    def __init__(self, log_dir):
        self.log_dir = log_dir

    def on_modified(self, event):
        if not event.is_directory:
            file_path = event.src_path
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                # Preparing the DCI Metadata Packet
                log_entry = {
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                    "source_file": os.path.basename(file_path),
                    "content": content,
                    "lab_status": "DCI_SYNC_ACTIVE"
                }
                
                # Dispatching to LM Studio API
                response = requests.post(
                    f"{LM_STUDIO_API}/v1/context", 
                    headers=HEADERS, 
                    data=json.dumps(log_entry)
                )
                
                if response.status_code == 200:
                    print(f"[DCI OK] Synced: {log_entry['source_file']}")
                else:
                    print(f"[DCI ERROR] Sync failed. Status: {response.status_code}")
            
            except Exception as e:
                print(f"[DCI CRITICAL] Error reading file: {e}")

def main():
    print("--- DCI Veridictum Lab: Librarian Core Starting ---")
    
    # Ensure log directory exists
    daily_log_path = os.path.join(WORKSPACE_PATH, 'logs', time.strftime('%Y-%m-%d'))
    if not os.path.exists(daily_log_path):
        os.makedirs(daily_log_path)
    
    # Initialize Watcher
    event_handler = LibrarianHandler(daily_log_path)
    observer = Observer()
    observer.schedule(event_handler, path=WORKSPACE_PATH, recursive=False)
    observer.start()
    
    print(f"[DCI] Monitoring workspace: {WORKSPACE_PATH}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[DCI] Librarian Core shutting down...")
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
