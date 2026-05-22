from .DeleteOldGalleries_ui import DOGUI
from .DeleteOldGalleries_server import DOGServer

def app():
    return DOGUI()

def server():
    return DOGServer()