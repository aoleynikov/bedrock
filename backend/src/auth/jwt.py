import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from src.config import settings


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({'exp': expire, 'iat': datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)
    to_encode.update({'exp': expire, 'iat': datetime.utcnow(), 'type': 'refresh'})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    return decode_token(token)


def create_oauth_state_token(state: str, provider: str, expires_minutes: int = 10) -> str:
    to_encode = {
        'state': state,
        'provider': provider,
        'type': 'oauth_state',
        'exp': datetime.utcnow() + timedelta(minutes=expires_minutes),
        'iat': datetime.utcnow()
    }
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_oauth_state_token(token: str) -> Optional[Dict[str, Any]]:
    payload = decode_token(token)
    if not payload or payload.get('type') != 'oauth_state':
        return None
    return payload
