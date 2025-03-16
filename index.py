import requests
import json
import os
from datetime import datetime

username = "SeasonableJourney"
roblosecurity_cookie = os.getenv('ROBLOSECURITY_COOKIE')
discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL')

def get_user_id(username):
    url = "https://users.roblox.com/v1/usernames/users"
    payload = {"usernames": [username], "excludeBannedUsers": True}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            return data['data'][0]['id']
    return None

def check_user_status(user_id):
    url = "https://presence.roblox.com/v1/presence/users"
    payload = {"userIds": [user_id]}
    headers = {"Cookie": f".ROBLOSECURITY={roblosecurity_cookie}"}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if 'userPresences' in data:
            user_presence = data['userPresences'][0]
            return (
                user_presence.get('userPresenceType') != 0,
                user_presence.get('lastLocation', 'Unknown'),
                user_presence.get('userPresenceType', 0),
                user_presence.get('lastOnline', '1970-01-01T00:00:00.000Z')
            )
    return False, 'Unknown', 0, '1970-01-01T00:00:00.000Z'

def get_latest_badge(user_id):
    url = f"https://badges.roblox.com/v1/users/{user_id}/badges?limit=10&sortOrder=Desc"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'data' in data and data['data']:
            latest_badge = data['data'][0]
            return latest_badge['name'], latest_badge['description'], latest_badge['id']
    return None, None, None

def send_discord_webhook(webhook_url, message):
    requests.post(webhook_url, json={"content": message})

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
    state_file = "state.json"
    user_id = get_user_id(username)
    if not user_id:
        print(f"Could not find user ID for {username}")
        return

    state = load_state(state_file)
    is_online, location, presence_type, last_online = check_user_status(user_id)
    status_changed = (
        is_online != state.get("last_status") or
        location != state.get("last_location") or
        presence_type != state.get("last_presence_type")
    )
    
    badge_name, badge_desc, badge_id = get_latest_badge(user_id)
    if badge_name and badge_name != state.get("last_badge"):
        badge_url = f"https://www.roblox.com/badges/{badge_id}"
        message = f"# 🏆 {username} has earned a new badge: **{badge_name}**\n\n{badge_desc}\n\n🔗 [View Badge]({badge_url})"
        send_discord_webhook(discord_webhook_url, message)
        state["last_badge"] = badge_name

    if status_changed:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if is_online:
            presence_str = "In game" if presence_type == 2 else "In Studio" if presence_type == 3 else "Online"
            circle = "🟢" if presence_type == 2 else "🟠" if presence_type == 3 else "🔵"
            message = f"# {circle} {username} is now {presence_str}!\n\nLast seen in: {location} ({current_time})"
        else:
            last_online_time = datetime.fromisoformat(last_online.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
            message = f"# 🔴 {username} is now offline\n\nLast online: {last_online_time}"
        send_discord_webhook(discord_webhook_url, message)
        state.update({"last_status": is_online, "last_location": location, "last_presence_type": presence_type})
    
    save_state(state_file, state)

if __name__ == "__main__":
    main()
