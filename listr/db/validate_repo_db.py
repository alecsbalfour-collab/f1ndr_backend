from .mongo_client_db import MongoClientDB, mongo_client_db


class ValidateRepoDB:
    def __init__(self, client: MongoClientDB):
        self.client = client

    def log_validation(self, data: dict) -> dict:
        return {
            "action": "log_validation",
            "data": data,
            "database": self.client.database,
        }


validate_repo_db = ValidateRepoDB(mongo_client_db)
