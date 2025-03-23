import socket
import threading
import json
import os
import sys
import logging
import hashlib
from datetime import datetime

# Absolute base path
BASE_PATH = r"C:\Users\EFE\Documents\GitHub\Python Projects\Python-Projects\Chat_application"

# Logging setup with file and console output
log_path = os.path.join(BASE_PATH, 'server.log')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(log_path)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)
logging.debug("Server started")

users_file = os.path.join(BASE_PATH, 'users.json')
friends_file = os.path.join(BASE_PATH, 'friends.json')
messages_file = os.path.join(BASE_PATH, 'messages.json')

def load_users():
    if os.path.exists(users_file):
        with open(users_file, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(users_file, 'w') as f:
        json.dump(users, f)
        f.flush()

def load_friends():
    if os.path.exists(friends_file):
        with open(friends_file, 'r') as f:
            return json.load(f)
    return {}

def save_friends(friends):
    with open(friends_file, 'w') as f:
        json.dump(friends, f)
        f.flush()

def load_messages():
    if os.path.exists(messages_file):
        with open(messages_file, 'r') as f:
            return json.load(f)
    return {}

def save_messages(messages):
    with open(messages_file, 'w') as f:
        json.dump(messages, f)
        f.flush()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def handle_client(client_socket):
    try:
        data = client_socket.recv(1024).decode()
        request = json.loads(data)
        action = request.get("action")
        username = request.get("username")
        password = request.get("password")
        friend = request.get("friend")
        message = request.get("message")
        logging.debug(f"Received request: {action} for {username}")

        users = load_users()
        friends = load_friends()
        messages = load_messages()

        if action == "SIGNUP":
            if username in users:
                client_socket.send("SIGNUP_FAIL".encode())
                logging.info(f"Signup failed: {username} already exists")
            else:
                users[username] = hash_password(password)
                friends[username] = []
                save_users(users)
                save_friends(friends)
                client_socket.send("SIGNUP_SUCCESS".encode())
                logging.info(f"Signup successful: {username}")

        elif action == "LOGIN":
            stored_hash = users.get(username)
            input_hash = hash_password(password)
            logging.debug(f"Login check: stored={stored_hash}, input={input_hash}")
            if stored_hash and stored_hash == input_hash:
                client_socket.send("LOGIN_SUCCESS".encode())
                logging.info(f"Login successful: {username}")
            else:
                client_socket.send("LOGIN_FAIL".encode())
                logging.info(f"Login failed: {username}")

        elif action == "ADD_FRIEND":
            if username not in users:
                client_socket.send("ADD_FRIEND_FAIL_USER".encode())
                logging.info(f"Add friend failed: {username} not found")
            elif friend not in users:
                client_socket.send("ADD_FRIEND_FAIL_FRIEND".encode())
                logging.info(f"Add friend failed: {friend} not found")
            elif friend in friends.get(username, []):
                client_socket.send("ADD_FRIEND_FAIL_EXISTS".encode())
                logging.info(f"Add friend failed: {friend} already in {username}'s list")
            else:
                friends[username].append(friend)
                save_friends(friends)
                client_socket.send("ADD_FRIEND_SUCCESS".encode())
                logging.info(f"Added {friend} to {username}'s friends")

        elif action == "SEND_MESSAGE":
            if username not in users or friend not in users:
                client_socket.send("MESSAGE_FAIL".encode())
                logging.info(f"Message failed: Invalid user/friend {username}-{friend}")
            else:
                chat_key = f"{username}-{friend}" if username < friend else f"{friend}-{username}"
                if chat_key not in messages:
                    messages[chat_key] = []
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                messages[chat_key].append({"sender": username, "text": message, "timestamp": timestamp})
                save_messages(messages)
                client_socket.send("MESSAGE_SENT".encode())
                logging.info(f"Message sent from {username} to {friend}: {message} at {timestamp}")

        elif action == "GET_MESSAGES":
            if username not in users or friend not in users:
                client_socket.send("MESSAGES_FAIL".encode())
                logging.info(f"Get messages failed: Invalid user/friend {username}-{friend}")
            else:
                chat_key = f"{username}-{friend}" if username < friend else f"{friend}-{username}"
                chat_history = messages.get(chat_key, [])
                client_socket.send(f"MESSAGES:{json.dumps(chat_history)}".encode())
                logging.debug(f"Sent chat history for {chat_key}")

    except Exception as e:
        logging.error(f"Error handling client: {e}")
    finally:
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 5555))
    server.listen(5)
    logging.info("Server listening on localhost:5555")
    while True:
        client_socket, addr = server.accept()
        logging.debug(f"Accepted connection from {addr}")
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

if __name__ == "__main__":
    start_server()