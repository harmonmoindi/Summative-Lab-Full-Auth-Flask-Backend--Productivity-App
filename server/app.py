from flask import Flask, request, session
from flask_migrate import Migrate
from flask_restful import Api, Resource
from sqlalchemy.exc import IntegrityError

from models import db, bcrypt, User, Note

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

def user_json(user):
    """The shape the client expects for a logged-in user."""
    return {'id': user.id, 'username': user.username}


class Signup(Resource):
    def post(self):
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')

        if password != data.get('password_confirmation'):
            return {'errors': ['Password and confirmation do not match.']}, 422

        try:
            user = User()
            user.username = username          # model validator runs here
            user.password_hash = password     # hashes, and validates length
            db.session.add(user)
            db.session.commit()
        except ValueError as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422
        except IntegrityError:
            db.session.rollback()
            return {'errors': ['Username is already taken.']}, 422

        session['user_id'] = user.id
        return user_json(user), 201


class Login(Resource):
    def post(self):
        data = request.get_json() or {}
        username = (data.get('username') or '').strip()
        password = data.get('password') or ''

        user = User.query.filter_by(username=username).first()
        if user and user.authenticate(password):
            session['user_id'] = user.id
            return user_json(user), 200

        # Same message for unknown user and wrong password, so we don't
        # reveal which usernames exist.
        return {'errors': ['Invalid username or password.']}, 401


class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        user = db.session.get(User, user_id) if user_id else None
        if user:
            return user_json(user), 200
        return {}, 401


class Logout(Resource):
    def delete(self):
        session.pop('user_id', None)
        return {}, 200


api.add_resource(Signup, '/signup')
api.add_resource(Login, '/login')
api.add_resource(CheckSession, '/check_session')
api.add_resource(Logout, '/logout')

if __name__ == '__main__':
    app.run(port=5555, debug=True)