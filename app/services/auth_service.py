import bcrypt
import sqlite3

from app.core.security import create_access_token
from app.repositories import user_repository
from app.errors.exceptions import AuthenticationError


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def authenticate(db: sqlite3.Connection, email: str, password: str) -> dict:
    user = user_repository.find_by_email(db, email)
    if not user or not verify_password(password, user["password"]):
        raise AuthenticationError("Invalid email or password")
    token = create_access_token({"sub": str(user["id"]), "email": user["email"]})
    return {
        "access_token": token,
        "user": {"id": user["id"], "email": user["email"], "name": user["name"]},
    }
