from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from database import SessionLocal
from models import User
from schemas import UserCreate, UserResponse, TokenResponse
from config import get_settings
from logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

if settings.has_insecure_secret_key and settings.is_production:
    # This is deliberately loud: a default JWT secret in production means
    # anyone can mint a valid token for any user. Fail visibly at startup
    # rather than silently shipping a forgeable auth system.
    logger.error(
        "SECURITY: running in production with the default secret_key. "
        "Set SECRET_KEY in your .env before deploying. Tokens issued with "
        "the default key are trivially forgeable."
    )


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def verify_token(token: str = Depends(oauth2_scheme)) -> str:
    """
    Decodes the JWT and confirms the user it names still exists -- a token
    issued to an account that was later deleted should not keep working
    for the rest of its (up to 24h by default) lifetime.
    """
    credentials_error = HTTPException(status_code=401, detail="Invalid or expired token")

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        email = payload.get("sub")
        if email is None:
            raise credentials_error
    except JWTError:
        raise credentials_error

    db = SessionLocal()
    try:
        user_exists = db.query(User).filter(User.email == email).first()
    finally:
        db.close()

    if not user_exists:
        raise credentials_error

    return email


@router.post("/register", response_model=TokenResponse)
def register(payload: UserCreate):
    """
    Takes email/password as a JSON body (not query params) so credentials
    never end up in a URL, server access log, or browser history. Logs the
    user in immediately on success -- one less round trip for the client.
    """
    db = SessionLocal()

    try:
        existing_user = db.query(User).filter(User.email == payload.email).first()

        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")

        hashed = hash_password(payload.password)

        user = User(email=payload.email, hashed_password=hashed)

        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token({"sub": user.email})

        return TokenResponse(access_token=token, token_type="bearer")

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        logger.exception("Registration failed for %s", payload.email)
        raise HTTPException(status_code=500, detail="Registration failed") from e

    finally:
        db.close()


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    email = form_data.username
    password = form_data.password

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
    finally:
        db.close()

    # Same error for "no such user" and "wrong password" -- distinguishing
    # them lets an attacker enumerate which emails have accounts.
    invalid_credentials = HTTPException(status_code=401, detail="Invalid email or password")

    if not user or not verify_password(password, user.hashed_password):
        raise invalid_credentials

    token = create_access_token({"sub": user.email})

    return TokenResponse(access_token=token, token_type="bearer")