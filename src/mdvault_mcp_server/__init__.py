__version__ = "0.2.1"
__all__ = ["create_server"]


def create_server():
    """Lazy import to avoid config validation on module load."""
    from .server import create_server as _create_server

    return _create_server()
