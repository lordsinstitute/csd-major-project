"""
Standalone script that creates the database and all tables.

Run from the project root:
    python -m database.init_db
"""

from flask import Flask
from sqlalchemy import inspect

from config import ensure_directories, get_config
from database.db import db, init_db


def main():
    """Create folders, create tables, and print a summary."""
    config_class = get_config()
    ensure_directories(config_class)

    app = Flask(__name__)
    app.config.from_object(config_class)
    init_db(app)

    with app.app_context():
        inspector = inspect(db.engine)
        print("Database:", app.config["SQLALCHEMY_DATABASE_URI"])
        for table_name in inspector.get_table_names():
            print("\nTable:", table_name)
            for column in inspector.get_columns(table_name):
                print("   -", column["name"], column["type"])


if __name__ == "__main__":
    main()