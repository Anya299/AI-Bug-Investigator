from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from passlib.context import CryptContext
from jose import jwt, JWTError

from database import SessionLocal
from models import User
from config import get_settings


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

settings = get_settings()

# NOTE: hardcoded here for now. Before deploying anywhere public, move this
# to settings/.env (e.g. settings.jwt_secret_key) so it's not sitting in
# source control. Fine for local dev, not fine for production.
SECRET_KEY = "change_this_secret_key"
ALGORITHM = "HS256"


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


# ---------------- PASSWORD ----------------

def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(
    plain_password,
    hashed_password
):
    return pwd_context.verify(
        plain_password,
        hashed_password
    )


# ---------------- JWT ----------------

def create_access_token(data: dict):

    to_encode = data.copy()

    # Configurable via settings.access_token_expire_minutes -- defaults to
    # a much longer dev-friendly window so local testing sessions (like
    # running evaluate_model.py repeatedly) don't keep hitting expiry.
    # Tighten this back down for production (e.g. 30-60 min) via .env.
    expire = datetime.utcnow() + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    to_encode.update({
        "exp": expire
    })

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def verify_token(
    token: str = Depends(oauth2_scheme)
):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")

        if email is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        return email


    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


# ---------------- REGISTER ----------------

@router.post("/register")
def register(
    email: str,
    password: str
):

    db = SessionLocal()

    existing = db.query(User).filter(
        User.email == email
    ).first()


    if existing:

        db.close()

        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )


    user = User(
        email=email,
        hashed_password=hash_password(password)
    )


    db.add(user)
    db.commit()
    db.close()


    return {
        "message":"User created successfully"
    }



# ---------------- LOGIN ----------------

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends()
):

    db = SessionLocal()


    user = db.query(User).filter(
        User.email == form_data.username
    ).first()


    db.close()


    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )


    if not verify_password(
        form_data.password,
        user.hashed_password
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )


    token = create_access_token(
        {
            "sub": user.email
        }
    )


    return {
        "access_token": token,
        "token_type":"bearer"
    }