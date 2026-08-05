from app.admin.view import health, metrics, ready
from app.example.model import item_decoder  # noqa: F401
from app.example.view import create_item, get_item, list_items
from main import _handle_app_exception, _handle_generic_exception  # noqa: F401
from manager import create_app, create_ci, create_worker, list_apps  # noqa: F401

_ = (health, metrics, ready, create_item, get_item, list_items)
