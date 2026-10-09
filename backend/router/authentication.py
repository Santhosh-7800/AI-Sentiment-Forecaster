from fastapi import APIRouter, HTTPException
from schemas import UserLogin,UserRegister
from hashing import verify_password
from services import user_service
from oauth2 import create_access_token


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

@router.post("/login")
def login(user: UserLogin):

    db_user = user_service.get_user_by_email(user.email)

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid username")

    if not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid password")

    # CREATE TOKEN
    access_token = create_access_token(
        data={"user_id": str(db_user["_id"])}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

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
