"""Reset the database and fill it with fake users and notes."""

from faker import Faker

from app import app
from models import db, User, Note

fake = Faker()

SEED_USERNAMES = ['alice', 'bob', 'carol']
SEED_PASSWORD = 'password123'
NOTES_PER_USER = 15

with app.app_context():
    print('Clearing existing data...')
    # Notes first, because they hold a foreign key to users.
    Note.query.delete()
    User.query.delete()
    db.session.commit()

    print('Seeding users and notes...')
    for username in SEED_USERNAMES:
        user = User()
        user.username = username
        user.password_hash = SEED_PASSWORD
        db.session.add(user)

        for _ in range(NOTES_PER_USER):
            db.session.add(Note(
                title=fake.sentence(nb_words=4).rstrip('.'),
                content=fake.paragraph(nb_sentences=3),
                user=user,
            ))

    db.session.commit()
    print(f'Done. {len(SEED_USERNAMES)} users, '
          f'{NOTES_PER_USER} notes each. Password for all: {SEED_PASSWORD}')