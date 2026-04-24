from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Iterator


PASSWORD_ITERATIONS = 210_000
SESSION_DAYS = 30


@dataclass(frozen=True)
class User:
    id: str
    username: str
    role: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ApiToken:
    id: str
    user_id: str
    name: str
    token_prefix: str
    created_at: str
    last_used_at: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class AuthStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.migrate()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def migrate(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    role TEXT NOT NULL DEFAULT 'admin',
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at)")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS api_tokens (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    token_prefix TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_used_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_api_tokens_token_hash ON api_tokens(token_hash)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_api_tokens_user_id ON api_tokens(user_id)")
            self.ensure_column(connection, "users", "role", "TEXT NOT NULL DEFAULT 'admin'")
            self.ensure_column(connection, "api_tokens", "user_id", "TEXT")
            first_user = connection.execute("SELECT id FROM users ORDER BY created_at ASC LIMIT 1").fetchone()
            if first_user:
                connection.execute(
                    "UPDATE users SET role = 'admin' WHERE role IS NULL OR TRIM(role) = ''"
                )
                connection.execute(
                    "UPDATE api_tokens SET user_id = ? WHERE user_id IS NULL OR TRIM(user_id) = ''",
                    (first_user["id"],),
                )

    def ensure_column(self, connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        columns = {
            row["name"]
            for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column not in columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def setup_required(self) -> bool:
        with self.connect() as connection:
            count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        return count == 0

    def create_initial_user(self, username: str, password: str, setup_token: str, configured_token: str) -> User:
        username = clean_username(username)
        validate_password(password)

        if not self.setup_required():
            raise ValueError("setup already completed")
        if configured_token and not hmac.compare_digest(setup_token, configured_token):
            raise ValueError("invalid setup token")
        if not configured_token and setup_token:
            raise ValueError("setup token is not configured")

        now = datetime.now(UTC).isoformat()
        user = User(id=secrets.token_hex(16), username=username, role="admin", created_at=now, updated_at=now)
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO users (id, username, role, password_hash, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user.id, user.username, user.role, hash_password(password), user.created_at, user.updated_at),
            )
        return user

    def list_users(self) -> list[User]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM users ORDER BY created_at ASC, username COLLATE NOCASE ASC"
            ).fetchall()
        return [user_from_row(row) for row in rows]

    def get_user(self, user_id: str) -> User | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return user_from_row(row) if row else None

    def create_user(self, username: str, password: str, role: str = "user") -> User:
        username = clean_username(username)
        validate_password(password)
        role = normalize_role(role)
        now = datetime.now(UTC).isoformat()
        user = User(id=secrets.token_hex(16), username=username, role=role, created_at=now, updated_at=now)
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO users (id, username, role, password_hash, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user.id, user.username, user.role, hash_password(password), user.created_at, user.updated_at),
            )
        return user

    def update_user(self, user_id: str, *, username: str | None = None, role: str | None = None) -> User:
        existing = self.get_user(user_id)
        if not existing:
            raise ValueError("user not found")
        new_username = clean_username(username) if username is not None else existing.username
        new_role = normalize_role(role) if role is not None else existing.role
        if existing.role == "admin" and new_role != "admin" and self.admin_count() <= 1:
            raise ValueError("last admin cannot be demoted")
        updated_at = datetime.now(UTC).isoformat()
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE users
                SET username = ?, role = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_username, new_role, updated_at, user_id),
            )
        return self.get_user(user_id)

    def delete_user(self, user_id: str) -> bool:
        existing = self.get_user(user_id)
        if not existing:
            return False
        if existing.role == "admin" and self.admin_count() <= 1:
            raise ValueError("last admin cannot be deleted")
        with self.connect() as connection:
            cursor = connection.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return cursor.rowcount > 0

    def change_password(self, user_id: str, current_password: str, new_password: str) -> None:
        validate_password(new_password)
        with self.connect() as connection:
            row = connection.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,)).fetchone()
            if not row:
                raise ValueError("user not found")
            if not verify_password(current_password, row["password_hash"]):
                raise ValueError("current password is invalid")
            connection.execute(
                "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
                (hash_password(new_password), datetime.now(UTC).isoformat(), user_id),
            )

    def admin_reset_password(self, user_id: str, new_password: str) -> User:
        validate_password(new_password)
        existing = self.get_user(user_id)
        if not existing:
            raise ValueError("user not found")
        with self.connect() as connection:
            connection.execute(
                "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
                (hash_password(new_password), datetime.now(UTC).isoformat(), user_id),
            )
        return self.get_user(user_id)

    def admin_count(self) -> int:
        with self.connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0])

    def authenticate(self, username: str, password: str) -> User | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM users WHERE username = ?", (username.strip(),)).fetchone()

        if not row or not verify_password(password, row["password_hash"]):
            return None
        return user_from_row(row)

    def create_session(self, user_id: str) -> str:
        now = datetime.now(UTC)
        session_id = secrets.token_urlsafe(32)
        with self.connect() as connection:
            connection.execute("DELETE FROM sessions WHERE expires_at <= ?", (now.isoformat(),))
            connection.execute(
                """
                INSERT INTO sessions (id, user_id, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    session_id,
                    user_id,
                    now.isoformat(),
                    (now + timedelta(days=SESSION_DAYS)).isoformat(),
                ),
            )
        return session_id

    def user_for_session(self, session_id: str) -> User | None:
        if not session_id:
            return None

        now = datetime.now(UTC).isoformat()
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT u.*
                FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.id = ? AND s.expires_at > ?
                """,
                (session_id, now),
            ).fetchone()
        return user_from_row(row) if row else None

    def delete_session(self, session_id: str) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    def create_api_token(self, user_id: str, name: str) -> dict[str, str | dict[str, str]]:
        name = clean_token_name(name)
        user = self.get_user(user_id)
        if not user:
            raise ValueError("user not found")
        now = datetime.now(UTC).isoformat()
        token = f"lv_pat_{secrets.token_urlsafe(32)}"
        api_token = ApiToken(
            id=secrets.token_hex(16),
            user_id=user.id,
            name=name,
            token_prefix=token[:14],
            created_at=now,
            last_used_at="",
        )
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO api_tokens (id, user_id, name, token_hash, token_prefix, created_at, last_used_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    api_token.id,
                    api_token.user_id,
                    api_token.name,
                    hash_api_token(token),
                    api_token.token_prefix,
                    api_token.created_at,
                    api_token.last_used_at,
                ),
            )
        return {"token": token, "api_token": api_token.to_dict()}

    def list_api_tokens(self, user_id: str) -> list[ApiToken]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, user_id, name, token_prefix, created_at, last_used_at
                FROM api_tokens
                WHERE user_id = ?
                ORDER BY created_at DESC
                """
                ,
                (user_id,),
            ).fetchall()
        return [api_token_from_row(row) for row in rows]

    def delete_api_token(self, token_id: str, user_id: str) -> bool:
        with self.connect() as connection:
            cursor = connection.execute("DELETE FROM api_tokens WHERE id = ? AND user_id = ?", (token_id, user_id))
        return cursor.rowcount > 0

    def user_for_api_token(self, token: str) -> User | None:
        if not token:
            return None

        token_hash = hash_api_token(token)
        now = datetime.now(UTC).isoformat()
        with self.connect() as connection:
            token_row = connection.execute(
                "SELECT id, user_id FROM api_tokens WHERE token_hash = ?",
                (token_hash,),
            ).fetchone()
            if not token_row:
                return None
            connection.execute("UPDATE api_tokens SET last_used_at = ? WHERE id = ?", (now, token_row["id"]))
            user_row = connection.execute("SELECT * FROM users WHERE id = ?", (token_row["user_id"],)).fetchone()
        return user_from_row(user_row) if user_row else None


def clean_username(username: str) -> str:
    cleaned = username.strip()
    if not cleaned:
        raise ValueError("username is required")
    if len(cleaned) > 80:
        raise ValueError("username is too long")
    return cleaned


def clean_token_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("token name is required")
    if len(cleaned) > 120:
        raise ValueError("token name is too long")
    return cleaned


def normalize_role(role: str) -> str:
    normalized = str(role or "").strip().lower()
    if normalized not in {"admin", "user"}:
        raise ValueError("role must be admin or user")
    return normalized


def validate_password(password: str) -> None:
    if len(password) < 12:
        raise ValueError("password must be at least 12 characters")


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected = password_hash.split("$", 3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False

    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), int(iterations))
    return hmac.compare_digest(digest.hex(), expected)


def hash_api_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def user_from_row(row: sqlite3.Row) -> User:
    return User(
        id=row["id"],
        username=row["username"],
        role=row["role"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def api_token_from_row(row: sqlite3.Row) -> ApiToken:
    return ApiToken(
        id=row["id"],
        user_id=row["user_id"],
        name=row["name"],
        token_prefix=row["token_prefix"],
        created_at=row["created_at"],
        last_used_at=row["last_used_at"],
    )
