#
#  Integrator.py
#  ABSToMediaTracker
#

import socketio
import requests
import json
import time
import logging
import os

logging.basicConfig(level=logging.DEBUG)

class AudiobookshelfListener:
    def __init__(self):
        self.audiobookshelf_url = os.environ.get('AUDIOBOOKSHELF_URL')
        self.username = os.environ.get('AUDIOBOOKSHELF_USERNAME')
        self.password = os.environ.get('AUDIOBOOKSHELF_PASSWORD')
        self.api_token = None
        self.mediatracker_url = os.environ.get('MEDIATRACKER_URL')
        self.mediatracker_token = os.environ.get('MEDIATRACKER_TOKEN')
        
        if not all([self.audiobookshelf_url, self.username, self.password, self.mediatracker_url, self.mediatracker_token]):
            raise ValueError("Missing required environment variables")

        self.sio = socketio.Client(logger=True, engineio_logger=True)
        self.setup_socket_events()
        self.is_authenticated = False

    def setup_socket_events(self):
        @self.sio.event
        def connect():
            logging.info("Connected to Audiobookshelf")
            if not self.api_token:
                logging.info("No API token found. Attempting to login.")
                if not self.login():
                    logging.error("Login failed. Disconnecting.")
                    self.sio.disconnect()
                    return
            self.authenticate()

        @self.sio.event
        def connect_error(data):
            logging.error(f"Connection error: {data}")
            self.is_authenticated = False

        @self.sio.event
        def disconnect():
            logging.info("Disconnected from Audiobookshelf")
            self.is_authenticated = False

        @self.sio.on('init')
        def on_init(data):
            logging.info(f"User was authorized: {data}")
            self.is_authenticated = True
            self.sio.emit('subscribe', {'events': ['user_item_progress_updated']})

        @self.sio.on('user_item_progress_updated')
        def on_user_item_progress_updated(data):
            self.handle_user_item_progress_update(data)

        @self.sio.on('*')
        def catch_all(event, data):
            logging.info(f"Received event: {event}")
            logging.info(f"Event data: {data}")

    def login(self):
        url = f"{self.audiobookshelf_url}/login"
        data = {
            "username": self.username,
            "password": self.password
        }
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            user_data = response.json()
            self.api_token = user_data['user']['token']
            logging.info(f"Login successful. API Token: {self.api_token[:10]}...")
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Login failed: {str(e)}")
            return False

    def authenticate(self):
        logging.info(f"Authenticating with Audiobookshelf using token: {self.api_token[:5]}...")
        self.sio.emit('auth', self.api_token)

    async def wait_for_connection(self, max_attempts=10, delay=1):
        attempts = 0
        while not self.sio.connected and attempts < max_attempts:
            await self.sio.sleep(delay)
            attempts += 1
        
        if not self.sio.connected:
            logging.error("Failed to connect after maximum attempts")
            return False
        return True

    def connect_to_audiobookshelf(self):
        while True:
            try:
                if not self.sio.connected:
                    logging.info("Attempting to connect to Audiobookshelf")
                    self.sio.connect(self.audiobookshelf_url)
                    self.sio.sleep(1)  # Give time for connection to establish
                    
                if not self.wait_for_connection():
                    logging.error("Failed to establish connection")
                    time.sleep(5)  # Wait before retry
                    continue
                    
                self.sio.wait()
            except Exception as e:
                logging.error(f"Error in connection: {str(e)}")
                time.sleep(5)  # Wait before attempting to reconnect

    def handle_user_item_progress_update(self, event_data):
        if not self.is_authenticated:
            logging.warning("Received update while not authenticated")
            return

        try:
            data = event_data.get('data', {})
            library_item_id = data.get('libraryItemId')
            if not library_item_id:
                logging.error("No libraryItemId found in progress update")
                return

            book_details = self.fetch_book_details(library_item_id)
            if not book_details:
                return

            asin = book_details.get('media', {}).get('metadata', {}).get('asin')
            if not asin:
                logging.error(f"No ASIN found for libraryItemId: {library_item_id}")
                return

            progress = data.get('progress', 0)
            current_time = data.get('currentTime', 0)
            duration = data.get('duration', 0)

            self.update_mediatracker(asin, progress, current_time, duration)
        except Exception as e:
            logging.error(f"Error handling progress update: {str(e)}")

    def fetch_book_details(self, library_item_id):
        url = f"{self.audiobookshelf_url}/api/items/{library_item_id}"
        headers = {'Authorization': f'Bearer {self.api_token}'}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch book details: {str(e)}")
            return None

    def update_mediatracker(self, asin, progress, current_time, duration):
        url = f"{self.mediatracker_url}/api/progress/by-external-id/"
        headers = {
            'Authorization': f'Bearer {self.mediatracker_token}',
            'Content-Type': 'application/json'
        }
        payload = {
            'progress': progress,
            'id': {
                'audibleId': asin
            },
            'mediaType': 'audiobook',
            'timestamp': int(time.time() * 1000)  # Current time in milliseconds
        }
        try:
            response = requests.put(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            logging.info(f"Successfully updated progress for book with ASIN {asin}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to update progress for book with ASIN {asin}. Error: {str(e)}")

if __name__ == "__main__":
    listener = AudiobookshelfListener()
    listener.connect_to_audiobookshelf()
