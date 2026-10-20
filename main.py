from airmouse.config import AppConfig
from airmouse.factory import build_app

if __name__ == "__main__":
    build_app(AppConfig()).run()
