from flask import Flask, request, session
from flask_migrate import Migrate
from flask_restful import Api, Resource

from models import db, bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

# Signs the session cookie. Placeholder for development only.
app.secret_key = 'dev-only-change-me'

db.init_app(app)
bcrypt.init_app(app)
migrate = Migrate(app, db)
api = Api(app)

# Define Routes here

if __name__ == '__main__':
    app.run(port=5555, debug=True)