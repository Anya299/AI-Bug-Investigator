from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from database import SessionLocal
from models import User


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


SECRET_KEY = "change-this-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
):
    return pwd_context.verify(
        plain_password,
        hashed_password
    )


def create_access_token(data: dict):

    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
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



@router.post("/register")
def register(
    email: str,
    password: str
):

    db = SessionLocal()

    try:

        existing_user = db.query(User).filter(
            User.email == email
        ).first()


        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User already exists"
            )


        hashed = hash_password(password)


        user = User(
            email=email,
            hashed_password=hashed
        )


        db.add(user)
        db.commit()


        return {
            "message": "User created successfully"
        }


    except Exception as e:

        db.rollback()

        print("REGISTER ERROR:", e)

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


    finally:
        db.close()



@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends()
):

    email = form_data.username
    password = form_data.password


    db = SessionLocal()

    user = db.query(User).filter(
        User.email == email
    ).first()

    db.close()


    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )


    if not verify_password(
        password,
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
        "token_type": "bearer"
    }