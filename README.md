# ConversationExporter (Discord Bot)

このボットは、Discordのチャンネル内の会話をエクスポートするために使用されます。会話は、返信関係に基づいて構造化され、テキスト、CSV、JSONの各形式でエクスポートされます。

## 機能

- `/会話エクスポート` コマンドを使用して、コマンドが実行されたチャンネルの会話をエクスポートします。
- エクスポートされた会話は、テキスト、CSV、JSONの各形式で保存されます。
- 設定ファイルを使用して、コマンドの使用を特定のロールまたはユーザーに制限できます。

## Quick Install

1. リポジトリをクローンします。
2. `pip install -r requirements.txt` を実行して、必要な依存関係をインストールします。
3. `create_setting.py` を実行し、設定を作成します。
4. `BOT_CONVERSATION_EXPORTER_TOKEN` 環境変数にボットのトークンを設定します。

## 設定の作成・追加

`create_setting.py` スクリプトを使用して、設定ファイルにギルド固有の設定を追加できます。
既に設定ファイルが存在する場合や同一のサーバーIDが存在する場合、スクリプトは設定ファイルに新しい設定を追加します。

```
python create_setting.py [file_location] [guild_id] [allowed_role_ids] [allowed_user_ids]
```

- `file_location`: 設定ファイルのパス
- `guild_id`: ギルドID
- `allowed_role_ids`: コマンドの使用を許可するロールIDのカンマ区切りリスト
- `allowed_user_ids`: コマンドの使用を許可するユーザーIDのカンマ区切りリスト

2. `BOT_CONVERSATION_EXPORTER_TOKEN` 環境変数にボットのトークンを設定します。

## 使用方法

1. ボットをDiscordサーバーに招待します。
2. `/会話エクスポート` コマンドを使用して、チャンネルの会話をエクスポートします。
3. エクスポートされた会話が、テキスト、CSV、JSONの各形式で返信されます。