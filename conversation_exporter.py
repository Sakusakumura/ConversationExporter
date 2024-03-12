import argparse
import csv
import json
import logging
import os
from typing import Dict

import discord
from discord.app_commands import CommandTree


class BotSettings:
    def __init__(self):
        self.command_allowed_role_id = []
        self.command_allowed_user_id = []

    @staticmethod
    def get_default():
        return BotSettings()

class BotSettingsRepository:
    def __init__(self, settings_file_path: str = "./config/bot_config.json"):
        self.settings: Dict[str, BotSettings] = {}
        self.load_settings(settings_file_path)

    def load_settings(self, filepath: str = "./config/bot_config.json"):
        try:
            with open(filepath, 'r') as config_file:
                config = json.load(config_file)
                for guild_id, settings_data in config.items():
                    settings = BotSettings()
                    settings.command_allowed_role_id = settings_data['command_allowed_role_id']
                    settings.command_allowed_user_id = settings_data['command_allowed_user_id']
                    self.settings[guild_id] = settings
        except FileNotFoundError as e:
            logging.log(level=logging.INFO, msg="config file not found. creating new one.")
            self.save_settings()

    def save_settings(self):
        config = {}
        for guild_id, settings in self.settings.items():
            config[guild_id] = {
                'command_allowed_role_id': settings.command_allowed_role_id,
                'command_allowed_user_id': settings.command_allowed_user_id
            }
        with open('./config/bot_config.json', 'w') as config_file:
            json.dump(config, config_file)

    def update_settings(self, guild_id: str, new_settings: BotSettings):
        self.settings[guild_id] = new_settings
        self.save_settings()

    def get_settings(self, guild_id: str) -> BotSettings:
        return self.settings.get(guild_id, BotSettings.get_default())

    def override_settings(self, guild_id: str, new_settings: BotSettings):
        self.settings[guild_id] = new_settings


class ConversationExporter(discord.Client):
    def __init__(self, settings_repository: BotSettingsRepository, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings_repository = settings_repository
        self.tree = CommandTree(self)
        self.synchronized = False

    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        if self.synchronized == False:
            await self.tree.client.tree.sync()
            self.synchronized = True

    async def on_export(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        channel_id = interaction.channel_id
        channel = interaction.channel
        user_id = interaction.user.id
        role_ids = [role.id for role in interaction.user.roles]
        settings = self.settings_repository.get_settings(str(guild_id))

        # role check
        if str(interaction.user.id) not in settings.command_allowed_user_id and not any(str(role_id) in settings.command_allowed_role_id for role_id in role_ids):
            await interaction.response.send_message("このコマンドの使用は許可されていません", ephemeral=True, delete_after=5)
            return

        # deferしないと、エラーが出る
        await interaction.response.defer()

        # fetch history
        history = {}
        async for fetched in channel.history():
            history[fetched.id] = fetched

        # structure conversations based on reply ids
        conversations = []
        processed_messages = set()

        # message.referenceで、返信先のメッセージを取得できる。message.reference.idは返信先のメッセージのID
        for message_id, message in history.items():
            if message.id in processed_messages:
                continue

            conversation = [message]
            processed_messages.add(message.id)

            while message.reference is not None:
                reply_id = message.reference.message_id
                if reply_id not in history or reply_id in processed_messages:
                    break

                reply_message = history[reply_id]
                conversation.insert(0, reply_message)
                processed_messages.add(reply_id)
                message = reply_message

            print(f"append: {conversation}")
            conversations.append(conversation)

        # export conversations to a file
        with open(f"{guild_id}_{channel_id}_conversations.txt", "w", encoding="utf-8") as file:
            for conversation in conversations:
                for message in conversation:
                    file.write(f"{message.author.name}: {message.content}\n")
                file.write("\n")

        # export conversations to a CSV file
        with open(f"{guild_id}_{channel_id}_conversations.csv", "w", encoding="utf-8", newline='') as file:
            writer = csv.writer(file)
            writer.writerow(
                ["sender_id", "sender_name", "timestamp", "conversation_id", "content", "attachments",
                 "reactions"])
            for conversation in conversations:
                last_message_id = conversation[-1].id
                for message in conversation:
                    attachments = [attachment.url for attachment in message.attachments]
                    reactions = [f"{reaction.emoji}:{reaction.count}" for reaction in message.reactions]
                    writer.writerow([
                        message.author.id,
                        message.author.name,
                        message.created_at.isoformat(),
                        last_message_id,
                        message.content,
                        ",".join(attachments),
                        ",".join(reactions)
                    ])

        # export conversations to a JSON file
        conversations_data = []
        for conversation in conversations:
            last_message_id = conversation[-1].id
            conversation_data = []
            for message in conversation:
                attachments = [attachment.url for attachment in message.attachments]
                reactions = [f"{reaction.emoji}:{reaction.count}" for reaction in message.reactions]
                message_data = {
                    "sender_id": message.author.id,
                    "sender_name": message.author.name,
                    "timestamp": message.created_at.isoformat(),
                    "conversation_id": last_message_id,
                    "content": message.content,
                    "attachments": attachments,
                    "reactions": reactions
                }
                conversation_data.append(message_data)
            conversations_data.append(conversation_data)

        with open(f"{guild_id}_{channel_id}_conversations.json", "w", encoding="utf-8") as file:
            json.dump(conversations_data, file, ensure_ascii=False, indent=4)

        await interaction.followup.send(files=[
            discord.File(f"{guild_id}_{channel_id}_conversations.csv"),
            discord.File(f"{guild_id}_{channel_id}_conversations.json"),
            discord.File(f"{guild_id}_{channel_id}_conversations.txt")
        ])


def main():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.guilds = True

    logging.basicConfig(level=logging.INFO)

    logging.log(level=logging.INFO, msg="Starting bot")

    activity = discord.Activity(name='`/会話エクスポート`', type=discord.ActivityType.playing)

    # コマンドライン引数のパーサーを作成
    parser = argparse.ArgumentParser(description='Discord会話エクスポートボット')
    parser.add_argument('--settings', '-s', type=str, default="./config/bot_config.json",
                        help='設定ファイルのパス (デフォルト: ./config/bot_config.json)')
    args = parser.parse_args()

    # 設定ファイルのパスをチェック
    if not os.path.isfile(args.settings):
        logging.error(f"設定ファイルが見つかりません: {args.settings}")
        return

    # load repository
    settings_repository = BotSettingsRepository(args.settings)

    client = ConversationExporter(settings_repository=settings_repository, intents=intents, activity=activity)

    @client.tree.command(name='会話エクスポート', description='このコマンドを実行したチャンネルの会話をエクスポートします。')
    async def export(interaction: discord.Interaction):
        await client.on_export(interaction)

    bot_token = os.getenv("BOT_CONVERSATION_EXPORTER_TOKEN", "")
    logging.log(level=logging.INFO, msg="bot_token: " + bot_token)
    client.run(bot_token)


if __name__ == "__main__":
    main()
