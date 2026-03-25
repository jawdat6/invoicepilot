from .aws import AWSConnector
from .twilio import TwilioConnector
from .mongodb import MongoDBConnector
from .zoho import ZohoConnector
from .godaddy import GoDaddyConnector
from .gcloud import GCloudConnector
from .stripe import StripeConnector
from .openphone import OpenPhoneConnector

ALL_CONNECTORS = [
    AWSConnector,
    TwilioConnector,
    MongoDBConnector,
    ZohoConnector,
    GoDaddyConnector,
    GCloudConnector,
    StripeConnector,
    OpenPhoneConnector,
]
