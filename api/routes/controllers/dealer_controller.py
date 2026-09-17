from utils.response_builder import success_response
from api.schemas.dealr_schemas import Dealer

class DealerController:
    def search(self, query: str):
        # Placeholder logic
        results = []
        return success_response({"results": results})

dealer_controller = DealerController()
