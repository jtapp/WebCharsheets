from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event

db = SQLAlchemy()

def setup_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///web-charsheets.db?mode=strict&check_same_thread=False'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    # Set WAL mode for SQLite
    with app.app_context():
        engine = db.get_engine(app=app)

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            if app.config['SQLALCHEMY_DATABASE_URI'].startswith("sqlite:"):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.close()
    
    with app.app_context():
        import models
        db.create_all()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()