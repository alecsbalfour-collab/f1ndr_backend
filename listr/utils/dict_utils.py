class DictUtils:
    def merge(self, base: dict, updates: dict) -> dict:
        return {**base, **updates}

    def compact(self, data: dict) -> dict:
        return {k: v for k, v in data.items() if v is not None}


dict_utils = DictUtils()
