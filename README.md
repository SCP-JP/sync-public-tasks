# sync-public-tasks

SCP-JPの非公開タスクリストから公開可能なものをミラーリングするスクリプト

## How to deploy

### 1. clone this repo
```sh
git clone https://github.com/SCP-JP/sync-public-tasks.git
```
### 2. add .env
```
NOTION_TOKEN="YOUR_NOTION_INTEGRATION_KEY"

SOURCE_DATABASE_ID="INPUT HERE"
DESTINATION_DATABASE_ID="INPUT HERE"
```
### 3. run
```
docker compose up -d
```
