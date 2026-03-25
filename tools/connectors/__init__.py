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

ALL_CONNECTORS = _connectors
