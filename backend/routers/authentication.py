# from fastapi import APIRouter, HTTPException
# from schemas import UserLogin,UserRegister
# from hashing import verify_password
# from services import user_service
# from oauth2 import create_access_token
# from server import generate_otp
# from datetime import datetime,timedelta
# router = APIRouter(
#     prefix="/api/auth",
#     tags=["Authentication"]
# )

# @router.post("/login")
# async def login(payload: dict):
#     user = user_service.get_user_by_email(user.email) 
#     if not user or not verify_password(payload.get("password"), user["password"]):
#         raise HTTPException(status_code=401, detail="Invalid credentials")

#     # Check if 2FA is enabled in user settings
#     if user.get("twoFactorEnabled"):
#         otp = generate_otp()
#         otp_collection.update_one(
#             {"email": user["email"]},
#             {"$set": {"otp": otp, "expires_at": datetime.utcnow() + timedelta(minutes=5)}},
#             upsert=True
#         )
#         return {"status": "2fa_required", "email": user["email"]}

#     # Normal login logic returns access_token
#     token = create_access_token(data={"user_id": str(user["_id"])})
#     return {"access_token": token, "token_type": "bearer"}
# # def login(user: UserLogin):

# #     db_user = user_service.get_user_by_email(user.email)

# #     if not db_user:
# #         raise HTTPException(status_code=404, detail="User not found")

# #     if not verify_password(user.password, db_user["password"]):
# #         raise HTTPException(status_code=401, detail="Invalid password")

# #     # CREATE TOKEN
# #     access_token = create_access_token(
# #         data={"user_id": str(db_user["_id"])}
# #     )

# #     return {
# #         "access_token": access_token,
# #         "token_type": "bearer"
# #     }

# @router.post("/register")
# def register(user: UserRegister):
#     try:
#         print("Incoming user:", user)

#         if user_service.get_user_by_email(user.email):
#             raise HTTPException(status_code=400, detail="Email already registered")

#         result = user_service.create_user(
#             user.firstname,
#             user.lastname,
#             user.email,
#             user.password
#         )

#         print("User created with ID:", result)

#         return {"message": "User created successfully"}

#     except Exception as e:
#         print("REGISTER ERROR:", str(e))
#         raise e
from fastapi import APIRouter, HTTPException, Depends
from schemas import UserLogin, UserRegister
<<<<<<< HEAD
from hashing import verify_password, hash_password, is_bcrypt_hash
=======
from hashing import verify_password
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)
from services import user_service
from oauth2 import create_access_token
from datetime import datetime, timedelta
import random
from database import db # Ensure you import your db instance

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

# Move OTP generation here to avoid circular imports with server.py
def generate_otp():
    return str(random.randint(100000, 999999))

otp_collection = db["otps"]
<<<<<<< HEAD
user_service.ensure_admin_user()

@router.post("/login")
async def login(payload: UserLogin): # Use your Pydantic schema for validation
    user_service.ensure_admin_user()

    # 1. Fetch user
    user = user_service.get_user_by_email(payload.email) 
    
    # 2. Verify existence and password
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username")

    if not verify_password(payload.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid password")

    # Migrate any legacy plaintext password to bcrypt on successful login.
    if not is_bcrypt_hash(user.get("password", "")):
        upgraded_hash = hash_password(payload.password)
        db["users"].update_one({"_id": user["_id"]}, {"$set": {"password": upgraded_hash}})
        user["password"] = upgraded_hash

    is_admin = bool(user.get("is_admin", False))

    # 3. Check if 2FA is enabled (check 'settings' or 'users' collection)
    # Usually, 2FA status is stored in the settings collection or user doc
    user_settings = db["settings"].find_one({"user_id": str(user["_id"])})
    is_2fa_enabled = user_settings.get("twoFactorEnabled", False) if user_settings else False

    if is_2fa_enabled:
        otp = generate_otp()
        # Store OTP with a 5-minute expiry
        otp_collection.update_one(
            {"email": user["email"]},
            {"$set": {
                "otp": otp, 
                "expires_at": datetime.utcnow() + timedelta(minutes=5)
            }},
            upsert=True
        )
        
        # DEBUG: In production, send this via Email/SMS
        print(f"--- 2FA OTP for {user['email']}: {otp} ---")
        
        return {
            "status": "2fa_required", 
            "email": user["email"],
            "message": "Please enter the OTP sent to your email",
            "is_admin": is_admin,
        }

    # 4. Normal login logic (No 2FA)
    token = create_access_token(data={"user_id": str(user["_id"]), "is_admin": is_admin})
    return {"access_token": token, "token_type": "bearer", "is_admin": is_admin}

@router.post("/verify-2fa")
async def verify_2fa(payload: dict):
    email = payload.get("email")
    user_code = payload.get("code")

=======

@router.post("/login")
async def login(payload: UserLogin): # Use your Pydantic schema for validation
    # 1. Fetch user
    user = user_service.get_user_by_email(payload.email) 
    
    # 2. Verify existence and password
    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 3. Check if 2FA is enabled (check 'settings' or 'users' collection)
    # Usually, 2FA status is stored in the settings collection or user doc
    user_settings = db["settings"].find_one({"user_id": str(user["_id"])})
    is_2fa_enabled = user_settings.get("twoFactorEnabled", False) if user_settings else False

    if is_2fa_enabled:
        otp = generate_otp()
        # Store OTP with a 5-minute expiry
        otp_collection.update_one(
            {"email": user["email"]},
            {"$set": {
                "otp": otp, 
                "expires_at": datetime.utcnow() + timedelta(minutes=5)
            }},
            upsert=True
        )
        
        # DEBUG: In production, send this via Email/SMS
        print(f"--- 2FA OTP for {user['email']}: {otp} ---")
        
        return {
            "status": "2fa_required", 
            "email": user["email"],
            "message": "Please enter the OTP sent to your email"
        }

    # 4. Normal login logic (No 2FA)
    token = create_access_token(data={"user_id": str(user["_id"])})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/verify-2fa")
async def verify_2fa(payload: dict):
    email = payload.get("email")
    user_code = payload.get("code")

>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)
    if not email or not user_code:
        raise HTTPException(status_code=400, detail="Email and Code required")

    # Find the OTP entry
    entry = otp_collection.find_one({"email": email, "otp": user_code})
    
    if not entry:
        raise HTTPException(status_code=400, detail="Invalid OTP code")
    
    if entry["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP has expired")

    # OTP is valid! Get the user to issue the final token
    user = user_service.get_user_by_email(email)
<<<<<<< HEAD
    is_admin = bool(user.get("is_admin", False)) if user else False
    token = create_access_token(data={"user_id": str(user["_id"]), "is_admin": is_admin})
=======
    token = create_access_token(data={"user_id": str(user["_id"])})
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)
    
    # Clean up: Delete OTP after successful use
    otp_collection.delete_one({"email": email})

<<<<<<< HEAD
    return {"access_token": token, "token_type": "bearer", "is_admin": is_admin}
=======
    return {"access_token": token, "token_type": "bearer"}
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)

@router.post("/register")
def register(user: UserRegister):
    try:
        print("Incoming user:", user)
        if user_service.get_user_by_email(user.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        result = user_service.create_user(
            user.firstname,
            user.lastname,
            user.email,
            user.password
        )
        print("User created with ID:", result)
        return {"message": "User created successfully"}
    except Exception as e:
        print("REGISTER ERROR:", str(e))
        raise e