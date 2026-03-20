from datetime import datetime as dt, timedelta, timezone
import os

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256" # HMAC with SHA-256
ACCESS_TOKEN_EXPIRE_MINUTES = 120 # 2 hours before forced logout

# Pwd hash config
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Give token format
bearer_scheme = HTTPBearer()

# Hash Password
def hash_password(pwd: str) -> str:
    return pwd_context.hash(pwd)


# Check password against hash
def verify_password(plain_pwd: str, hash_pwd: str) -> bool:
    return pwd_context.verify(plain_pwd, hash_pwd)


# Generate signed JWT access token for login success
def gen_access_token(data: dict, expires_mins: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy() # Gen token for username
    expire = dt.now(timezone.utc) + timedelta(minutes=expires_mins)
    to_encode.update({"exp": expire}) # Add expiry time
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Check admin credentials
def check_creds(username: str, password: str, db: Session):
    # Find username
    admin = db.query(models.Admin).filter(models.Admin.username == username).first()
    
    # Check username exists
    if not admin:
        return None
    
    # Check password against username
    if not verify_password(password, admin.password_hash):
        return None
    
    return admin


# Return current admin
# When accessing authorised endpoints, attach this to check authenticity
def get_current_admin(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(get_db)
):
    # Store bearer token
    token = credentials.credentials

    # Try verify token signature, checking expiry
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub") # Sub stores username

        # No valid subject
        if username is None:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token"
        )

    # Fake or expired token raises JWTError
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token"
        )
    
    # Double check for username in admin table
    admin = db.query(models.Admin).filter(models.Admin.username == username).first()

    # Invalid admin
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token"
        )
    
    return admin    