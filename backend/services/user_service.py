# def get_user_by_email(email: str):
#     # Temporary mock user for testing
#     if email == "test@gmail.com":
#         return {
#             "_id": "12345",
#             "email": "test@gmail.com",
#             "password": "1234"  # plain for testing only
#         }
#     return None
import os

from hashing import hash_password, verify_password, is_bcrypt_hash
from database import db

users_collection = db["users"]
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@gmail.com").strip().lower()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


def get_user_by_email(email: str):
    return users_collection.find_one({"email": email.strip().lower()})


def ensure_admin_user():
    admin_user = users_collection.find_one({"email": ADMIN_EMAIL})
    admin_hash = hash_password(ADMIN_PASSWORD)

    if not admin_user:
        users_collection.insert_one({
            "firstname": "Admin",
            "lastname": "User",
            "email": ADMIN_EMAIL,
            "password": admin_hash,
            "is_admin": True,
        })
        return

    updates = {"is_admin": True}
    stored_password = admin_user.get("password", "")

    # Keep admin credentials aligned with configured defaults.
    if (not is_bcrypt_hash(stored_password)) or (not verify_password(ADMIN_PASSWORD, stored_password)):
        updates["password"] = admin_hash

    users_collection.update_one({"_id": admin_user["_id"]}, {"$set": updates})

def create_user(firstname: str, lastname: str, email: str, password: str):
    hashed_pw = hash_password(password)

    new_user = {
        "firstname": firstname,
        "lastname": lastname,
        "email": email.strip().lower(),
        "password": hashed_pw,
        "is_admin": False,
    }

    result = users_collection.insert_one(new_user)
    return str(result.inserted_id)