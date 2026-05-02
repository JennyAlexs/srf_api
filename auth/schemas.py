from pydantic import BaseModel, Field

class Token(BaseModel):
    """Ответ при успешном логине"""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Данные внутри токена (для внутренней логики)"""
    user_id: int | None = None
    role: str | None = None

class UserLogin(BaseModel):
    """Входные данные для логина (если не используем OAuth2PasswordRequestForm)"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
