import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import TokenData
from app.config import settings
from typing import Optional
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status

def get_password_hash(password: str) -> str:
    # bcrypt.hashpw expects bytes. We encode the password and then decode the result back to string for storage.
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # bcrypt.checkpw expects bytes for both the password and the hash.
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Dependencia que protege una ruta. Extrae el token de la cabecera HTTP,
    lo decodifica, valida que no haya expirado y retorna el usuario de la BD.
    """
    # Definimos el error estándar de credenciales inválidas
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales de acceso.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 1. Decodificar el Token usando nuestra clave secreta y algoritmo
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # 2. Extraer el 'sub' (Subject) que guardamos en el login (el username)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
        token_data = TokenData(username=username)
    except JWTError:
        # Si el token fue alterado, está mal construido o expiró, saltará este error
        raise credentials_exception
        
    # 3. Buscar al usuario en la base de datos para verificar que aún existe
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
        
    # 4. Verificar que el usuario no esté baneado o inactivo
    if not user.is_active:
        raise HTTPException(status_code=400, detail="El usuario se encuentra inactivo.")
        
    # Retornamos el objeto usuario completo. Ahora la ruta sabe EXACTAMENTE quién le está hablando.
    return user

