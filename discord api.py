import requests
from jsonutils import jsonfile
import base64
from config import TOKEN
content = jsonfile('./cogs/metadata/saved.json')


url = "https://discord.com/api/v10/applications/1094412371390374029/commands"

# This is an example CHAT_INPUT or Slash Command, with a type of 1
json = {
    "name": "clear",
    "description": "Use this command for clear the messages in your current chat",
    "type": 1,
    "options": [
        {
            "name": "amount",
            "description": "how many messages to clear",
            "type": 4,
            "required": False
        },
    ]
}

# For authorization, you can use either your bot token
headers = {
    "Authorization": f"Bot {base64.urlsafe_b64decode(bytes.fromhex(TOKEN)).decode()}"
}

# or a client credentials token for your app with the applications.commands.update scope
#headers = {
    #"Authorization": "Bearer <my_credentials_token>"
#}

r = requests.post(url, headers=headers, json=json)
print('statuscode',r.status_code)
print(r.content.decode())