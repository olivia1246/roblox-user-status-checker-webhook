import requests
import json
from datetime import datetime

def get_user_id(username):
    url = "https://users.roblox.com/v1/usernames/users"
    payload = {
        "usernames": [username],
        "excludeBannedUsers": True
    }
    response = requests.post(url, json=payload)
    print(f"get_user_id response: {response.status_code}, {response.text}")  # Debug print
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            return data['data'][0]['id']
    return None

def check_user_status(user_id):
    url = "https://presence.roblox.com/v1/presence/users"
    payload = {
        "userIds": [user_id]
    }
    response = requests.post(url, json=payload)
    print(f"check_user_status response: {response.status_code}, {response.text}")  # Debug print
    if response.status_code == 200:
        data = response.json()
        print("Response Data:", data)  # Debug print
        if 'userPresences' in data:
            user_presence = data['userPresences'][0]
            is_online = user_presence.get('userPresenceType') != 0
            last_location = user_presence.get('lastLocation', 'Unknown')
            presence_type = user_presence.get('userPresenceType', 0)
            last_online = user_presence.get('lastOnline', '1970-01-01T00:00:00.000Z')
            return is_online, last_location, presence_type, last_online
    return False, 'Unknown', 0, '1970-01-01T00:00:00.000Z'

def send_discord_webhook(webhook_url, message):
    payload = {
        "content": message
    }
    response = requests.post(webhook_url, json=payload)
    print(f"send_discord_webhook response: {response.status_code}, {response.text}")  # Debug print

def load_state(state_file):
    try:
        with open(state_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_state(state_file, state):
    with open(state_file, 'w') as f:
        json.dump(state, f)

def main():
    username = "Eloisa04"
    discord_webhook_url = "https://discord.com/api/webhooks/1264619798235582556/0q2-1IYvUzaZQimyrB9zgThkkVI41t8AIYrrnYt6ZBBr4URN20fzUmcpibUxWqMnmPRV"
    state_file = "state.json"

    user_id = get_user_id(username)
    print(f"User ID: {user_id}")  # Debug print
    if not user_id:
        print(f"Could not find user ID for username: {username}")
        return

    state = load_state(state_file)
    last_status = state.get("last_status", None)
    last_location = state.get("last_location", None)
    last_presence_type = state.get("last_presence_type", None)

    is_online, location, presence_type, last_online = check_user_status(user_id)
    print(f"Status: {is_online}, Location: {location}, Presence Type: {presence_type}, Last Online: {last_online}")  # Debug print
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    status_changed = (
        is_online != last_status or
        location != last_location or
        presence_type != last_presence_type
    )
    
    if status_changed:
        if is_online:
            if presence_type == 2:
                presence_str = "In game"
                circle = "🟢"
            elif presence_type == 3:
                presence_str = "In Studio"
                circle = "🟠"
            else:
                presence_str = "Online"
                circle = "🔵"
            message = f"{circle} {username} is now {presence_str}! Last seen in: {location} (as of {current_time})"
        else:
            last_online_time = datetime.fromisoformat(last_online.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
            message = f"🔴 {username} is now offline (Last online: {last_online_time})"
        
        send_discord_webhook(discord_webhook_url, message)
        
        state["last_status"] = is_online
        state["last_location"] = location
        state["last_presence_type"] = presence_type
        save_state(state_file, state)

if __name__ == "__main__":
    main()
