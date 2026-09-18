class UnifyPipeline:
    def run(self, query: dict) -> dict:
        return {
            "query": query,
            "status": "unify_pipeline_executed",
        }

unify_pipeline = UnifyPipeline()
