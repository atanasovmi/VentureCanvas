"""Shared Flask extension instances.

Extensions are instantiated here without binding to an app so they can be
imported anywhere and initialized later inside the app factory via `init_app`.
"""

from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
