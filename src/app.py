from flask import Flask

from db import setup_db, db

app = Flask(__name__)
setup_db(app)

import routes

if __name__ == "__main__":
    app.run()