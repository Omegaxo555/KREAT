from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token
from app.security import get_password_hash, verify_password, create_access_token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])

# endpoint de registro de un nuevo usuario
@router.post("/register", response_model=UserResponse)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado"
        )

    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )

    user_dict = user_data.model_dump()
    plain_password = user_dict.pop("password")

    hashed_password = get_password_hash(plain_password)

    new_user = User(**user_dict, hashed_password=hashed_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

# ==========================================
#            ENDPOINT DE LOGIN
# ==========================================
@router.post("/login", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    Verifica las credenciales y devuelve un Token JWT válido por 24 horas.
    """
    # 1. Buscar al usuario por su nombre de usuario (OAuth2 usa por defecto la propiedad 'username')
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # 2. Si no existe el usuario O la contraseña no coincide, lanzamos el mismo error genérico.
    # Nota de seguridad: No le digas al usuario cuál de los dos falló (si el usuario o la clave) 
    # para evitar ataques de enumeración de usuarios.
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Si el usuario está desactivado por el administrador, denegar acceso
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Este usuario se encuentra inactivo."
        )
    
    # 4. Generar el Token JWT empaquetando el username en el payload
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},  # 'sub' (Subject) es el estándar JWT para identificar al usuario
        expires_delta=access_token_expires
    )
    
    # 5. Retornar el token bajo la estructura exacta requerida por el esquema 'Token'
    return {"access_token": access_token, "token_type": "bearer"}


