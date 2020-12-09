from .base_settings import *

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += ["retention_data_pipeline"]

EDW_SERVER = "edw"

if os.getenv("ENV") == "localdev":
    DEBUG = True
    EDW_USER = os.getenv("EDW_USER")
    EDW_PASSWORD = os.getenv("EDW_PASSWORD")
    RESTCLIENTS_SWS_OAUTH_BEARER = os.getenv("RESTCLIENTS_SWS_OAUTH_BEARER")

RESTCLIENTS_SWS_DAO_CLASS = "Live"
RESTCLIENTS_SWS_HOST = "https://ws.admin.washington.edu"
RESTCLIENTS_SWS_TIMING_START = 0
