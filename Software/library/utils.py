"""
File : Session Management Utility
Author: Suyog Buradkar
Date: 25 April 2024
"""

def get_last_session_id():
    try:
        with open(SESSION_FILE_PATH, "r") as file:
            last_session_id = file.read().strip()
        return last_session_id
    except FileNotFoundError:
        return None

def save_session_id(session_id):
    with open(SESSION_FILE_PATH, "w") as file:
        file.write(session_id)

def increment_session_id(session_id):
    session_number = int(session_id.split("#")[1])
    next_session_number = session_number + 1
    return f"session#{next_session_number:05d}"
