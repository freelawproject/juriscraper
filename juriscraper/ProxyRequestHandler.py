import os


class ProxyRequestHandler:
    """Class to handle requests through DECODO residential proxies."""

    def __init__(self, *args, **kwargs):
        USERNAME = os.environ.get("DECODO_USER")
        PASSWORD = os.environ.get("DECODO_PASSWORD")
        PROXY_ADDRESS = os.environ.get("DECODO_PROXY")
        PORT = os.environ.get("DECODO_PORT")
        if not USERNAME or not PASSWORD or not PROXY_ADDRESS or not PORT:
            raise ValueError("Missing DECODO proxy environment variables")
        self.proxy = f"http://{USERNAME}:{PASSWORD}@{PROXY_ADDRESS}:{PORT}"
