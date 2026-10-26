from flask import Flask, request, session
from flask_migrate import Migrate
from flask_restful import Api, Resource
from sqlalchemy.exc import IntegrityError
from functools import wraps

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

def login_required(func):
    """Reject the request with 401 unless a valid user is logged in."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id or not db.session.get(User, user_id):
            session.pop('user_id', None)
            return {'errors': ['Unauthorized. Please log in.']}, 401
        return func(*args, **kwargs)
    return wrapper

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

def note_json(note):
    return {
        'id': note.id,
        'title': note.title,
        'content': note.content,
        'created_at': note.created_at.isoformat() if note.created_at else None,
        'updated_at': note.updated_at.isoformat() if note.updated_at else None,
        'user_id': note.user_id,
    }


def get_own_note(note_id):
    """Fetch a note only if it belongs to the logged-in user.

    Notes owned by other users look exactly like notes that don't exist,
    so one user can't discover another user's record ids.
    """
    return Note.query.filter_by(id=note_id, user_id=session['user_id']).first()


class NoteList(Resource):
    method_decorators = [login_required]

    def get(self):
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        if page < 1 or per_page < 1:
            return {'errors': ['page and per_page must be positive integers.']}, 400
        per_page = min(per_page, 100)  # cap page size

        pagination = (
            Note.query.filter_by(user_id=session['user_id'])
            .order_by(Note.id.desc())  # newest first
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        return {
            'notes': [note_json(n) for n in pagination.items],
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
        }, 200

    def post(self):
        data = request.get_json() or {}
        try:
            note = Note(
                title=data.get('title'),
                content=data.get('content'),
                user_id=session['user_id'],
            )
            db.session.add(note)
            db.session.commit()
        except ValueError as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422
        return note_json(note), 201


class NoteDetail(Resource):
    method_decorators = [login_required]

    def get(self, note_id):
        note = get_own_note(note_id)
        if not note:
            return {'errors': ['Note not found.']}, 404
        return note_json(note), 200

    def patch(self, note_id):
        note = get_own_note(note_id)
        if not note:
            return {'errors': ['Note not found.']}, 404

        data = request.get_json() or {}
        fields = [f for f in ('title', 'content') if f in data]
        if not fields:
            return {'errors': ['Provide title and/or content to update.']}, 422

        try:
            for field in fields:
                setattr(note, field, data[field])
            db.session.commit()
        except ValueError as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422
        return note_json(note), 200

    def delete(self, note_id):
        note = get_own_note(note_id)
        if not note:
            return {'errors': ['Note not found.']}, 404
        db.session.delete(note)
        db.session.commit()
        return '', 204


api.add_resource(Signup, '/signup')
api.add_resource(Login, '/login')
api.add_resource(CheckSession, '/check_session')
api.add_resource(Logout, '/logout')
api.add_resource(NoteList, '/notes')
api.add_resource(NoteDetail, '/notes/<int:note_id>')

if __name__ == '__main__':
    app.run(port=5555, debug=True)