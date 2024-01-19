# Notionのタスクリストから「公開種別：公開」のタスクを取得し、別DBにミラーリングするスクリプト
#   autor: ukwhatn
#   date : 2024/01/20
from datetime import datetime
from time import sleep

import dotenv
import os
from notion_client import Client

# 環境変数の読み込み
dotenv.load_dotenv()

# 各種環境変数の取得
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
SOURCE_DATABASE_ID = os.environ.get("SOURCE_DATABASE_ID")
DESTINATION_DATABASE_ID = os.environ.get("DESTINATION_DATABASE_ID")
TEST_DATABASE_ID = os.environ.get("TEST_DATABASE_ID")

# スリープ時間
DURATION = 60 * 60 * 24


def get_all_entries(client: Client, database_id: str, query: dict = None):
    """next_cursorを自動で処理して、全てのエントリを取得する"""
    # 初回取得
    params = {
        "database_id": database_id,
    }
    if query is not None:
        params["filter"] = query

    resp = client.databases.query(**params)

    results = resp["results"]

    # next_cursorがある場合は、再度クエリを実行して取得する
    while resp["has_more"]:
        resp = client.databases.query(
            database_id=database_id,
            filter=query,
            start_cursor=resp["next_cursor"]
        )
        results += resp["results"]

    return results


def build_properties(task: dict):
    """create/update用のpropertiesを作成する"""
    return {
        "タイトル": {
            "title": [
                {
                    "text": {
                        "content": task['properties']['タイトル']['title'][0]['plain_text']
                    }
                }
            ]
        },
        "カテゴリ": {
            "select": {
                "name": task['properties']['カテゴリ']['select']['name']
            }
        },
        "ステータス": {
            "status": {
                "name": task['properties']['ステータス']['status']['name']
            }
        },
        "担当チーム": {
            "multi_select": [
                {"name": team['name']} for team in task['properties']['担当チーム']['multi_select']
            ]
        }
    }


def main():
    # Notionのクライアントを作成
    client = Client(auth=NOTION_TOKEN)

    # ソースDBのタスクリストを取得
    source_tasks = get_all_entries(
        client=client,
        database_id=SOURCE_DATABASE_ID,
        query={
            "and": [
                {
                    "property": "公開種別",
                    "select": {
                        "equals": "公開"
                    }
                },
                {
                    "property": "ステータス",
                    "status": {
                        "is_not_empty": True
                    }
                }
            ]
        }
    )

    # ミラー先DBのタスクリストを取得
    destination_tasks = get_all_entries(
        client=client,
        database_id=DESTINATION_DATABASE_ID,
        query={
            "property": "ステータス",
            "status": {
                "is_not_empty": True
            }
        }
    )

    # 既知のタスクIDをリスト化
    known_tasks = {
        task['properties']['sourceId']['rich_text'][0]['plain_text']: task["id"]
        for task in destination_tasks
    }

    print(f"Source: {len(source_tasks)}")
    print(f"Destination: {len(destination_tasks)}")

    # ソースDBのタスクごとに、ミラー先DBに存在しない場合は追加する
    for task in source_tasks:
        if task['id'] in known_tasks:
            # 既知のタスクは更新
            print(f"Update: {task['properties']['タイトル']['title'][0]['plain_text']}")
            # 更新
            client.pages.update(
                page_id=known_tasks[task['id']],
                properties=build_properties(task)
            )
        else:
            # 未知のタスクは作成
            print(f"Create: {task['properties']['タイトル']['title'][0]['plain_text']}")

            # propertiesにsourceIdを追加
            properties = build_properties(task)
            properties["sourceId"] = {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": task['id']
                        }
                    }
                ]
            }
            # 作成
            client.pages.create(
                parent={
                    "database_id": DESTINATION_DATABASE_ID
                },
                properties=properties
            )


if __name__ == "__main__":
    while True:
        print(f"Start: {str(datetime.now())} {SOURCE_DATABASE_ID} -> {DESTINATION_DATABASE_ID}")
        main()
        print(f"End: {str(datetime.now())} {SOURCE_DATABASE_ID} -> {DESTINATION_DATABASE_ID}")
        print(f"Sleep: {DURATION} sec")
        sleep(DURATION)
