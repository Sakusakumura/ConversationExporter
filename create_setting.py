import sys
import json
from json import JSONDecodeError
from typing import Dict

class BotSettings:
    def __init__(self):
        self.command_allowed_role_id = []
        self.command_allowed_user_id = []

    @staticmethod
    def get_default():
        return BotSettings()

def add_settings(file_location: str, guild_id: str, allowed_role_ids: str, allowed_user_ids: str):
    settings = BotSettings()
    settings.command_allowed_role_id = allowed_role_ids.split(',')
    settings.command_allowed_user_id = allowed_user_ids.split(',')

    try:
        with open(file_location, 'r') as config_file:
            config: Dict[str, BotSettings] = json.load(config_file)
    except FileNotFoundError:
        config = {}
    except JSONDecodeError:
        config = {}

    config[guild_id] = {
        'command_allowed_role_id': settings.command_allowed_role_id,
        'command_allowed_user_id': settings.command_allowed_user_id
    }

    with open(file_location, 'w') as config_file:
        json.dump(config, config_file)

    print(f"Settings added for guild {guild_id} at {file_location}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python add_settings.py [file_location] [guild_id] [allowed_role_ids] [allowed_user_ids]")
        sys.exit(1)

    file_location = sys.argv[1]
    guild_id = sys.argv[2]
    allowed_role_ids = sys.argv[3]
    allowed_user_ids = sys.argv[4]

    add_settings(file_location, guild_id, allowed_role_ids, allowed_user_ids)