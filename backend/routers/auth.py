from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from database import get_db
from models.auth import LoginRequest, TokenResponse, UserMe
from services.auth_service import verify_password, create_token, decode_token

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    return payload


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text(
            "SELECT id, nombres, paterno, usuario, contrasena "
            "FROM seg_usuario "
            "WHERE usuario = :u AND estado = 'HAB' AND habilitado = 1"
        ),
        {"u": body.usuario},
    )
    row = result.mappings().first()

    if not row or not verify_password(body.contrasena, row["contrasena"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    token = create_token({
        "id": row["id"],
        "nombres": row["nombres"],
        "paterno": row["paterno"],
        "usuario": row["usuario"],
    })
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserMe)
async def me(current_user: dict = Depends(get_current_user)):
    return UserMe(**current_user)
