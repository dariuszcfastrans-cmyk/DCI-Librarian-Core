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

# --- Configuration via Environment Variables with sensible fallbacks ---
LM_STUDIO_API = os.getenv("LM_STUDIO_API", "http://localhost:1234")
HEADERS = {"Content-Type": "application/json"}
WORKSPACE_PATH = os.getenv("WORKSPACE_PATH", os.path.expanduser('~/VSCodeWorkspace'))
RECURSIVE_MONITORING = os.getenv("RECURSIVE_MONITORING", "true").lower() in ("true", "1", "yes")
MAX_FILE_SIZE_KB = int(os.getenv("MAX_FILE_SIZE_KB", "1024"))  # 1 MB default limit

class LibrarianHandler(FileSystemEventHandler):
    """
    DCI Librarian Handler: 
    Monitors workspace changes and synchronizes context with LM Studio.
    """
    def __init__(self):
        super().__init__()

    def get_daily_log_path(self):
        """
        Dynamically returns the daily log directory inside the workspace logs,
        ensuring the directory exists.
        """
        today = time.strftime('%Y-%m-%d')
        daily_dir = os.path.normpath(os.path.join(WORKSPACE_PATH, 'logs', today))
        os.makedirs(daily_dir, exist_ok=True)
        return daily_dir

    def log_local_event(self, source_file, status, message=""):
        """
        Logs a sync event locally in JSON format inside the dynamic daily log directory.
        """
        try:
            daily_dir = self.get_daily_log_path()
            log_file_path = os.path.join(daily_dir, 'sync_events.log')

            log_line = {
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                "file": source_file,
                "status": status,
                "message": message
            }
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_line) + '\n')
        except Exception as e:
            print(f"[DCI CRITICAL] Failed to write local log: {e}")

    def should_ignore(self, file_path):
        """
        Determines whether the given file path should be ignored to prevent
        infinite synchronization loops, binary reading errors, or unnecessary processing.
        """
        norm_path = os.path.normpath(file_path)
        parts = norm_path.split(os.sep)

        # 1. Ignore specific directory names or hidden directories
        ignored_dirs = {'.git', '.github', '__pycache__', 'node_modules', '.venv', 'venv', 'logs'}
        for part in parts:
            if part in ignored_dirs or part.startswith('.'):
                return True

        # 2. Ignore typical binary, temporary, or package lock formats
        ignored_extensions = {
            '.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip',
            '.tar', '.gz', '.tgz', '.rar', '.db', '.sqlite', '.sqlite3',
            '.pyc', '.pyo', '.pyd', '.class', '.o', '.obj', '.dll', '.exe',
            '.log'  # Ignore .log extension to explicitly avoid infinite loop on log writes
        }
        _, ext = os.path.splitext(file_path)
        if ext.lower() in ignored_extensions:
            return True

        ignored_files = {'package-lock.json', 'poetry.lock', 'yarn.lock', 'uv.lock'}
        if os.path.basename(file_path) in ignored_files:
            return True

        # 3. Ignore files that exceed the maximum size limit
        try:
            if os.path.exists(file_path):
                size_kb = os.path.getsize(file_path) / 1024
                if size_kb > MAX_FILE_SIZE_KB:
                    print(f"[DCI INFO] Ignored (too large, > {MAX_FILE_SIZE_KB}KB): {os.path.basename(file_path)}")
                    return True
        except OSError:
            # If we cannot access the file size, safe to ignore
            return True

        return False

    def on_modified(self, event):
        if not event.is_directory:
            file_path = event.src_path

            # Check if this file should be ignored
            if self.should_ignore(file_path):
                return

            try:
                # Read content safely with UTF-8 encoding, handling potential read errors
                with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                    content = file.read()
                
                # Preparing the DCI Metadata Packet
                log_entry = {
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                    "source_file": os.path.basename(file_path),
                    "content": content,
                    "lab_status": "DCI_SYNC_ACTIVE"
                }
                
                # Dispatching to LM Studio API with a robust timeout
                try:
                    response = requests.post(
                        f"{LM_STUDIO_API}/v1/context",
                        headers=HEADERS,
                        data=json.dumps(log_entry),
                        timeout=5  # Prevents thread hang if LM Studio is unresponsive
                    )

                    if response.status_code == 200:
                        print(f"[DCI OK] Synced: {log_entry['source_file']}")
                        self.log_local_event(log_entry['source_file'], "SUCCESS", "Synced successfully")
                    else:
                        err_msg = f"HTTP {response.status_code}: {response.text}"
                        print(f"[DCI ERROR] Sync failed. Status: {response.status_code}")
                        self.log_local_event(log_entry['source_file'], "FAILED", err_msg)
                
                except requests.exceptions.RequestException as req_err:
                    print(f"[DCI ERROR] Sync failed due to network error: {req_err}")
                    self.log_local_event(log_entry['source_file'], "NETWORK_ERROR", str(req_err))
            
            except Exception as e:
                print(f"[DCI CRITICAL] Error reading file {os.path.basename(file_path)}: {e}")
                self.log_local_event(os.path.basename(file_path), "CRITICAL_ERROR", str(e))

def main():
    print("--- DCI Veridictum Lab: Librarian Core Starting ---")
    
    # Resolve and ensure workspace path exists
    abs_workspace = os.path.abspath(WORKSPACE_PATH)
    if not os.path.exists(abs_workspace):
        os.makedirs(abs_workspace, exist_ok=True)
    
    # Initialize Watcher
    event_handler = LibrarianHandler()
    observer = Observer()
    observer.schedule(event_handler, path=abs_workspace, recursive=RECURSIVE_MONITORING)
    observer.start()
    
    print(f"[DCI] Monitoring workspace: {abs_workspace} (Recursive: {RECURSIVE_MONITORING})")
    print(f"[DCI] LM Studio API target: {LM_STUDIO_API}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[DCI] Librarian Core shutting down...")
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
