import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import requests

# We set environment variables before importing librarian_core
os.environ["WORKSPACE_PATH"] = tempfile.mkdtemp()
os.environ["RECURSIVE_MONITORING"] = "true"
os.environ["MAX_FILE_SIZE_KB"] = "10"

import librarian_core
from librarian_core import LibrarianHandler

class TestLibrarianCore(unittest.TestCase):
    def setUp(self):
        self.handler = LibrarianHandler()
        self.temp_dir = os.environ["WORKSPACE_PATH"]

    def tearDown(self):
        # Clean up files in the temporary workspace
        for root, dirs, files in os.walk(self.temp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

    def test_should_ignore_folders(self):
        # Ignore files inside hidden or specific directories
        self.assertTrue(self.handler.should_ignore(os.path.join(self.temp_dir, ".git", "config")))
        self.assertTrue(self.handler.should_ignore(os.path.join(self.temp_dir, "node_modules", "package.json")))
        self.assertTrue(self.handler.should_ignore(os.path.join(self.temp_dir, "logs", "2026-01-01", "sync.log")))

        # Do not ignore standard source files
        self.assertFalse(self.handler.should_ignore(os.path.join(self.temp_dir, "src", "index.js")))
        self.assertFalse(self.handler.should_ignore(os.path.join(self.temp_dir, "main.py")))

    def test_should_ignore_extensions_and_lockfiles(self):
        self.assertTrue(self.handler.should_ignore(os.path.join(self.temp_dir, "image.png")))
        self.assertTrue(self.handler.should_ignore(os.path.join(self.temp_dir, "log_file.log")))
        self.assertTrue(self.handler.should_ignore(os.path.join(self.temp_dir, "package-lock.json")))
        self.assertTrue(self.handler.should_ignore(os.path.join(self.temp_dir, "poetry.lock")))

    def test_should_ignore_large_files(self):
        large_file = os.path.join(self.temp_dir, "large.txt")
        # Write 15 KB (limit is 10 KB in setup)
        with open(large_file, 'wb') as f:
            f.write(b"a" * 15 * 1024)

        self.assertTrue(self.handler.should_ignore(large_file))

    def test_get_daily_log_path(self):
        daily_dir = self.handler.get_daily_log_path()
        self.assertTrue(os.path.exists(daily_dir))
        self.assertTrue(daily_dir.startswith(self.temp_dir))

    def test_log_local_event(self):
        self.handler.log_local_event("test_file.py", "SUCCESS", "All good")
        daily_dir = self.handler.get_daily_log_path()
        log_file = os.path.join(daily_dir, "sync_events.log")
        self.assertTrue(os.path.exists(log_file))

        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("test_file.py", content)
            self.assertIn("SUCCESS", content)
            self.assertIn("All good", content)

    @patch('requests.post')
    def test_on_modified_success(self, mock_post):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Create a test file
        test_file = os.path.join(self.temp_dir, "sample.py")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("print('Hello World')")

        # Mock watch event
        event = MagicMock()
        event.is_directory = False
        event.src_path = test_file

        self.handler.on_modified(event)

        # Assert requests.post was called with correct data and 5s timeout
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['timeout'], 5)
        self.assertIn("v1/context", args[0])

        payload = kwargs['data']
        self.assertIn("sample.py", payload)
        self.assertIn("print('Hello World')", payload)

if __name__ == "__main__":
    unittest.main()
