import os

USER = os.environ.get("ORACLE_USER", "concordance")
PASSWORD = os.environ.get("ORACLE_PASSWORD")
DSN = os.environ.get("ORACLE_DSN", "localhost:1521/FREEPDB1")

CONFIG_DIR = os.environ.get("ORACLE_CONFIG_DIR") or None
WALLET_DIR = os.environ.get("ORACLE_WALLET_DIR") or None
WALLET_PASSWORD = os.environ.get("ORACLE_WALLET_PASSWORD") or None


def connect_kwargs():
    """Returns the settings used to connect to Oracle."""

    if not PASSWORD:
        raise RuntimeError(
            "ORACLE_PASSWORD environment variable is not set"
        )

    kwargs = {
        "user": USER,
        "password": PASSWORD,
        "dsn": DSN
    }

    if CONFIG_DIR:
        kwargs["config_dir"] = CONFIG_DIR

    if WALLET_DIR:
        kwargs["wallet_location"] = WALLET_DIR

    if WALLET_PASSWORD:
        kwargs["wallet_password"] = WALLET_PASSWORD

    return kwargs