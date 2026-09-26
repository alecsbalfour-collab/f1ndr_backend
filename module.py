from api.main import app
import dealr
import f1ndr
import listr
import sellr
import trinn

f1ndr_backend = {
    "f1ndr": f1ndr.run,
    "trinn": trinn.run,
    "sellr": sellr.run,
    "listr": listr.run,
    "dealr": dealr.run,
}
