from pydantic import BaseModel, EmailStr,Field

class UserRegister(BaseModel):
    firstname: str
    lastname:str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str
class RealtimeAnalyzeRequest(BaseModel):
    product: str = Field(..., min_length=2, max_length=100)
    max_articles: int = Field(default=25, ge=5, le=100)
    force_refresh: bool = False
<<<<<<< HEAD
    llm_provider: str = Field(default="auto", pattern="^(auto|groq|gemini)$")
=======
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)


class ProfileUpdateRequest(BaseModel):
    firstname: str | None = Field(default=None, min_length=1, max_length=60)
    lastname: str | None = Field(default=None, min_length=1, max_length=60)
    email: str | None = Field(default=None, min_length=5, max_length=120)
class ForgotPasswordRequest(BaseModel):
    email: str
<<<<<<< HEAD
    new_password: str
=======
    new_password: str

class ChatRequest(BaseModel):
    message: str
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)
