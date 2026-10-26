from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from sqlalchemy.orm import validates

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    _password_hash = db.Column(db.String, nullable=False)

    notes = db.relationship(
        'Note', back_populates='user', cascade='all, delete-orphan'
    )

    @property
    def password_hash(self):
        # The hash is write-only: it should never be readable from the model.
        raise AttributeError('Password hashes may not be viewed.')

    @password_hash.setter
    def password_hash(self, password):
        if not password or len(password) < 8:
            raise ValueError('Password must be at least 8 characters.')
        self._password_hash = bcrypt.generate_password_hash(
            password.encode('utf-8')
        ).decode('utf-8')

    def authenticate(self, password):
        """Return True if the given plain-text password matches the stored hash."""
        return bcrypt.check_password_hash(
            self._password_hash, password.encode('utf-8')
        )

    @validates('username')
    def validate_username(self, key, username):
        if not username or not username.strip():
            raise ValueError('Username is required.')
        if len(username.strip()) < 3:
            raise ValueError('Username must be at least 3 characters.')
        return username.strip()


class Note(db.Model):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, server_default=db.func.now(), onupdate=db.func.now()
    )
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    user = db.relationship('User', back_populates='notes')

    @validates('title')
    def validate_title(self, key, title):
        if not title or not title.strip():
            raise ValueError('Title is required.')
        if len(title.strip()) > 100:
            raise ValueError('Title must be 100 characters or fewer.')
        return title.strip()

    @validates('content')
    def validate_content(self, key, content):
        if not content or not content.strip():
            raise ValueError('Content is required.')
        return content