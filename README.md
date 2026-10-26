# Productivity App: Notes API (Flask Backend)

A secure Flask REST API for a personal notes app. Users register and log in with session-based authentication, and each user can create, read, update, and delete **only their own** notes. The notes list is paginated.

Built with Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-RESTful, Flask-Bcrypt, and Faker. It is designed to work with the provided sessions client (`client-with-sessions`).

## Features

- Registration, login, logout, and session checking with Flask sessions
- Passwords hashed with bcrypt, never stored in plain text
- Notes CRUD where every route requires login
- Users cannot see, edit, or delete each other's notes
- Pagination on the notes list
- Model-level validations and database constraints
- JSON error responses in the form `{"errors": ["..."]}`

## Installation

Requires Python 3.12 (3.8.13+ should also work) and [Pipenv](https://pipenv.pypa.io/).

```bash
git clone https://github.com/harmonmoindi/Summative-Lab-Full-Auth-Flask-Backend--Productivity-App.git
cd Summative-Lab-Full-Auth-Flask-Backend--Productivity-App
pipenv install
pipenv shell
cd server
flask db upgrade
python seed.py
```

`flask db upgrade` creates the SQLite database (`server/instance/app.db`). `python seed.py` resets it and adds three users (`alice`, `bob`, `carol`, all with password `password123`) with 15 fake notes each. It is safe to run more than once.

## Running the app

From the `server/` folder, with the pipenv shell active:

```bash
python app.py
```

The API runs at http://localhost:5555. Optionally set `SECRET_KEY` in your environment to sign session cookies with your own key.

### Using the provided client

In a separate terminal, from the `client-with-sessions` folder of the provided client repo:

```bash
npm install
npm start
```

The client runs at http://localhost:4000 and proxies API requests to port 5555.

## Endpoints

All requests and responses use JSON.

### Authentication

| Method | Route            | Description                                                                                                      |
| ------ | ---------------- | ---------------------------------------------------------------------------------------------------------------- |
| POST   | `/signup`        | Create a user and log in. Body: `username`, `password`, `password_confirmation`. Returns `{id, username}` (201). |
| POST   | `/login`         | Log in. Body: `username`, `password`. Returns `{id, username}` (200), or 401 on bad credentials.                 |
| GET    | `/check_session` | Returns the logged-in user as `{id, username}` (200), or `{}` with 401 if not logged in.                         |
| DELETE | `/logout`        | Ends the session. Returns `{}` (200).                                                                            |

### Notes (login required)

| Method | Route         | Description                                                                                                      |
| ------ | ------------- | ---------------------------------------------------------------------------------------------------------------- |
| GET    | `/notes`      | List the current user's notes, newest first. Query params: `page` (default 1), `per_page` (default 10, max 100). |
| POST   | `/notes`      | Create a note. Body: `title`, `content`. Returns the note (201).                                                 |
| GET    | `/notes/<id>` | Get one of the current user's notes.                                                                             |
| PATCH  | `/notes/<id>` | Update `title` and/or `content`. Returns the updated note.                                                       |
| DELETE | `/notes/<id>` | Delete a note. Returns 204 with no body.                                                                         |

Paginated response shape for `GET /notes`:

```json
{
  "notes": [
    {
      "id": 1,
      "title": "...",
      "content": "...",
      "created_at": "...",
      "updated_at": "...",
      "user_id": 1
    }
  ],
  "page": 1,
  "per_page": 10,
  "total": 15,
  "pages": 2
}
```

### Status codes and errors

| Code            | Meaning                                                                                      |
| --------------- | -------------------------------------------------------------------------------------------- |
| 200 / 201 / 204 | Success / created / deleted                                                                  |
| 400             | Invalid pagination values                                                                    |
| 401             | Not logged in, or wrong username or password                                                 |
| 404             | Note not found. This is also returned for other users' notes, so their ids are not revealed. |
| 422             | Validation failed, for example a missing title, a short password, or a duplicate username    |

## Validations

- **User:** username required, at least 3 characters, and unique. Password at least 8 characters.
- **Note:** title required and at most 100 characters. Content required.
- **Database constraints:** `NOT NULL` on required columns, `UNIQUE` on `username`, and a foreign key from `notes.user_id` to `users.id`.

## Project structure

```
server/
├── app.py          # app setup, auth and notes routes
├── models.py       # User and Note models
├── seed.py         # resets and seeds the database
└── migrations/     # Flask-Migrate migration files
Pipfile             # dependencies
```
