from pydantic import BaseModel


class LoginRequest(BaseModel):
    usuario: str
    contrasena: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserMe(BaseModel):
    id: int
    nombres: str
    paterno: str
    usuario: str
