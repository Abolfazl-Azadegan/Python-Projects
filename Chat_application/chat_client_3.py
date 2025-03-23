import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext
import logging
import os
import sys
import socket
import json
from datetime import datetime

# Absolute base path
BASE_PATH = r"C:\Users\EFE\Documents\GitHub\Python Projects\Python-Projects\Chat_application"

# Logging setup with absolute path
log_path = os.path.join(BASE_PATH, 'client.log')
try:
    logging.basicConfig(filename=log_path, level=logging.DEBUG, 
                        format='%(asctime)s - %(levelname)s - %(message)s')
except Exception as e:
    logging.basicConfig(level=logging.DEBUG,  # Fallback to console
                        format='%(asctime)s - %(levelname)s - %(message)s')
    print(f"Failed to initialize file logging: {e}")
logging.debug("Client started")

# File paths
friends_file = os.path.join(BASE_PATH, 'friends.json')

def load_friends():
    if os.path.exists(friends_file):
        with open(friends_file, 'r') as f:
            return json.load(f)
    return {}

class ChatClient:
    def __init__(self):
        # Login window
        self.root = tk.Tk()
        self.root.title("Login")
        self.root.geometry("600x400")
        self.root.configure(bg="#f0f0f0")
        
        self.font = ("Arial", 12)
        
        login_frame = tk.Frame(self.root, bg="#f0f0f0")
        login_frame.pack(expand=True)
        
        tk.Label(login_frame, text="Username:", font=self.font, bg="#f0f0f0").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.username_entry = tk.Entry(login_frame, width=30, font=self.font)
        self.username_entry.grid(row=0, column=1, padx=10, pady=10)
        
        tk.Label(login_frame, text="Password:", font=self.font, bg="#f0f0f0").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.password_entry = tk.Entry(login_frame, width=30, show="*", font=self.font)
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)
        
        tk.Button(login_frame, text="Signup", command=self.signup, font=self.font, width=10).grid(row=2, column=0, padx=10, pady=20)
        tk.Button(login_frame, text="Login", command=self.login, font=self.font, width=10).grid(row=2, column=1, padx=10, pady=20)
        
        self.username = None
        self.sock = None
        self.chat_windows = {}  # Store chat window data by friend name

    def send_to_server(self, action, username, password=None, friend=None, message=None):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect(('localhost', 5555))
            request = {"action": action, "username": username}
            if password:
                request["password"] = password
            if friend:
                request["friend"] = friend
            if message:
                request["message"] = message
            self.sock.send(json.dumps(request).encode())
            response = self.sock.recv(4096).decode()
            logging.debug(f"Sent {action} request for {username}, received: {response}")
            return response
        except Exception as e:
            logging.error(f"Error in send_to_server: {e}")
            return "ERROR"
        finally:
            if self.sock:
                self.sock.close()

    def signup(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        response = self.send_to_server("SIGNUP", username, password)
        messagebox.showinfo("Signup", "Signup successful" if response == "SIGNUP_SUCCESS" else f"Signup failed: {response}")

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        response = self.send_to_server("LOGIN", username, password)
        logging.debug(f"Login response: {response}")
        if response == "LOGIN_SUCCESS":
            self.username = username
            self.root.destroy()
            self.show_friends_window()
        else:
            messagebox.showerror("Login", f"Invalid credentials, response: {response}")

    def add_friend(self):
        friend_name = self.friend_entry.get().strip()
        if friend_name:
            response = self.send_to_server("ADD_FRIEND", self.username, friend=friend_name)
            if response == "ADD_FRIEND_SUCCESS":
                messagebox.showinfo("Success", f"Added {friend_name} to your friends!")
                self.update_friends_list()
                self.friend_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Error", f"Failed to add {friend_name}: {response}")
        else:
            messagebox.showerror("Error", "Please enter a friend name.")

    def update_friends_list(self):
        self.friends_list.delete(0, tk.END)
        friends = load_friends()
        user_friends = friends.get(self.username, [])
        if user_friends:
            for friend in user_friends:
                self.friends_list.insert(tk.END, friend)
        else:
            self.friends_list.insert(tk.END, "No friends yet.")

    def open_chat(self, event):
        selected = self.friends_list.curselection()
        if selected:
            friend = self.friends_list.get(selected[0])
            if friend != "No friends yet.":
                self.show_chat_window(friend)

    def show_chat_window(self, friend):
        if friend in self.chat_windows:
            self.chat_windows[friend]["window"].lift()  # Bring existing window to front
            return
        
        chat_window = tk.Toplevel()
        chat_window.title(f"Chat with {friend}")
        chat_window.geometry("600x500")
        chat_window.configure(bg="#f0f0f0")
        
        # Chat display area
        chat_frame = tk.Frame(chat_window, bg="#f0f0f0")
        chat_frame.pack(padx=20, pady=10, fill="both", expand=True)
        chat_display = scrolledtext.ScrolledText(chat_frame, width=60, height=20, font=self.font, wrap=tk.WORD)
        chat_display.pack(fill="both", expand=True)
        chat_display.config(state="disabled")
        
        # Message input area
        input_frame = tk.Frame(chat_window, bg="#f0f0f0")
        input_frame.pack(padx=20, pady=10, fill="x")
        message_entry = tk.Entry(input_frame, width=40, font=self.font)
        message_entry.pack(side="left", padx=10, pady=5)
        send_button = tk.Button(input_frame, text="Send", command=lambda: self.send_message(friend), font=self.font, width=10)
        send_button.pack(side="left", padx=10, pady=5)
        
        # Store chat window data
        self.chat_windows[friend] = {
            "window": chat_window,
            "display": chat_display,
            "entry": message_entry
        }
        
        # Load chat history and start refresh
        self.load_chat_history(friend)
        self.refresh_chat(friend)
        
        chat_window.protocol("WM_DELETE_WINDOW", lambda: self.on_chat_close(friend))

    def load_chat_history(self, friend):
        if friend not in self.chat_windows:
            return
        try:
            response = self.send_to_server("GET_MESSAGES", self.username, friend=friend)
            logging.debug(f"Loading chat history for {friend}, response: {response}")
            if response.startswith("MESSAGES:"):
                messages = json.loads(response[len("MESSAGES:"):])
                chat_display = self.chat_windows[friend]["display"]
                chat_display.config(state="normal")
                chat_display.delete(1.0, tk.END)
                for msg in messages:
                    sender = msg["sender"]
                    text = msg["text"]
                    timestamp = msg.get("timestamp", "Unknown time")
                    display_text = f"[{timestamp}] {text}"
                    if sender == self.username:
                        chat_display.insert(tk.END, f"{display_text}\n", ("right",))
                        chat_display.tag_configure("right", justify="right", background="blue", foreground="white")
                    else:
                        chat_display.insert(tk.END, f"{display_text}\n", ("left",))
                        chat_display.tag_configure("left", justify="left", background="green", foreground="white")
                chat_display.config(state="disabled")
                chat_display.see(tk.END)
            else:
                logging.error(f"Invalid response for GET_MESSAGES: {response}")
        except Exception as e:
            logging.error(f"Error loading chat history for {friend}: {e}")

    def send_message(self, friend):
        if friend not in self.chat_windows:
            return
        message = self.chat_windows[friend]["entry"].get().strip()
        if message:
            response = self.send_to_server("SEND_MESSAGE", self.username, friend=friend, message=message)
            if response == "MESSAGE_SENT":
                self.chat_windows[friend]["entry"].delete(0, tk.END)
                self.load_chat_history(friend)

    def refresh_chat(self, friend):
        if friend in self.chat_windows and self.chat_windows[friend]["window"].winfo_exists():
            self.load_chat_history(friend)
            self.chat_windows[friend]["window"].after(2000, lambda: self.refresh_chat(friend))

    def on_chat_close(self, friend):
        if friend in self.chat_windows:
            self.chat_windows[friend]["window"].destroy()
            del self.chat_windows[friend]

    def show_friends_window(self):
        self.friends_window = tk.Tk()
        self.friends_window.title(f"Chat - {self.username}")
        self.friends_window.geometry("800x600")
        self.friends_window.configure(bg="#f0f0f0")
        
        main_frame = tk.Frame(self.friends_window, bg="#f0f0f0")
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        tk.Label(main_frame, text=f"Welcome, {self.username}!", font=("Arial", 16, "bold"), bg="#f0f0f0").pack(pady=10)
        
        add_frame = tk.Frame(main_frame, bg="#f0f0f0")
        add_frame.pack(pady=20, fill="x")
        tk.Label(add_frame, text="Add a Friend:", font=self.font, bg="#f0f0f0").pack(side="left", padx=10)
        self.friend_entry = tk.Entry(add_frame, width=30, font=self.font)
        self.friend_entry.pack(side="left", padx=10)
        tk.Button(add_frame, text="Add Friend", command=self.add_friend, font=self.font, width=10).pack(side="left", padx=10)
        
        tk.Label(main_frame, text="Your Friends:", font=("Arial", 14), bg="#f0f0f0").pack(pady=10)
        self.friends_list = tk.Listbox(main_frame, width=50, height=15, font=self.font)
        self.friends_list.pack(pady=10, fill="both", expand=True)
        self.friends_list.bind("<Double-1>", self.open_chat)
        self.update_friends_list()
        
        self.friends_window.mainloop()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    client = ChatClient()
    client.run()