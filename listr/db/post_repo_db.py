from .mongo_client_db import MongoClientDB, mongo_client_db


class PostRepoDB:
    def __init__(self, client: MongoClientDB):
        self.client = client

    def create(self, data: dict) -> dict:
        return {
            "action": "create",
            "data": data,
            "database": self.client.database,
        }

    def get(self, post_id: str) -> dict:
        return {
            "action": "get",
            "post_id": post_id,
            "database": self.client.database,
        }


post_repo_db = PostRepoDB(mongo_client_db)
