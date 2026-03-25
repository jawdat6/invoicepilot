import importlib.util
import inspect
from pathlib import Path

from .base import BaseConnector

_connectors = []

try:
    from .aws import AWSConnector
    _connectors.append(AWSConnector)
except ImportError:
    pass

try:
    from .twilio import TwilioConnector
    _connectors.append(TwilioConnector)
except ImportError:
    pass

try:
    from .mongodb import MongoDBConnector
    _connectors.append(MongoDBConnector)
except ImportError:
    pass

try:
    from .zoho import ZohoConnector
    _connectors.append(ZohoConnector)
except ImportError:
    pass

try:
    from .godaddy import GoDaddyConnector
    _connectors.append(GoDaddyConnector)
except ImportError:
    pass

try:
    from .gcloud import GCloudConnector
    _connectors.append(GCloudConnector)
except ImportError:
    pass

try:
    from .stripe import StripeConnector
    _connectors.append(StripeConnector)
except ImportError:
    pass

try:
    from .openphone import OpenPhoneConnector
    _connectors.append(OpenPhoneConnector)
except ImportError:
    pass

_user_connector_dir = Path.home() / ".invoicepilot" / "connectors"
if _user_connector_dir.exists():
    for _py_file in sorted(_user_connector_dir.glob("*.py")):
        try:
            _spec = importlib.util.spec_from_file_location(_py_file.stem, _py_file)
            _mod = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            for _name, _cls in inspect.getmembers(_mod, inspect.isclass):
                if (
                    issubclass(_cls, BaseConnector)
                    and _cls is not BaseConnector
                    and _cls not in _connectors
                ):
                    _connectors.append(_cls)
        except Exception as _e:
            print(f"  Warning: could not load user connector {_py_file.name}: {_e}")

ALL_CONNECTORS = _connectors
