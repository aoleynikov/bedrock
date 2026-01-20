import secrets
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from src.auth.service import auth_service
from src.auth.dependencies import get_current_user
from src.auth.jwt import create_oauth_state_token, verify_oauth_state_token
from src.models.domain import User
from src.logging.logger import get_logger
from src.exceptions import UnauthorizedException
from src.config import settings

router = APIRouter()
logger = get_logger(__name__, 'api')


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    strategy: str = 'credentials'


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post('/auth/login', response_model=TokenResponse)
async def login(
    request: Request,
    login_data: LoginRequest
):
    result = await auth_service.authenticate(
        strategy_name=login_data.strategy,
        request=request,
        email=login_data.email,
        password=login_data.password
    )
    
    if not result.success:
        logger.warning(
            'Login failed',
            extra={
                'correlation_id': request.state.correlation_id,
                'strategy': login_data.strategy,
            }
        )
        raise UnauthorizedException()
    
    tokens = auth_service.create_tokens(
        user_id=result.user_id,
        email=result.user_data.get('email', login_data.email),
        role=result.user_data.get('role', 'user')
    )
    
    logger.info(
        f'User logged in: {result.user_id}',
        extra={
            'correlation_id': request.state.correlation_id,
            'user_id': result.user_id,
            'strategy': login_data.strategy,
        }
    )
    
    return TokenResponse(**tokens)


@router.post('/auth/refresh', response_model=TokenResponse)
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest
):
    payload = auth_service.verify_refresh_token(refresh_data.refresh_token)
    
    if not payload:
        raise UnauthorizedException()
    
    user_id = payload.get('sub')
    email = payload.get('email')
    
    if not user_id or not email:
        raise UnauthorizedException()
    
    tokens = auth_service.create_tokens(
        user_id=user_id,
        email=email,
        role=payload.get('role', 'user')
    )
    
    return TokenResponse(**tokens)


@router.get('/auth/me')
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    return {
        'id': current_user.id,
        'email': current_user.email,
        'name': current_user.name,
    }


@router.post('/auth/logout')
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    logger.info(
        f'User logged out: {current_user.id}',
        extra={
            'correlation_id': request.state.correlation_id,
            'user_id': current_user.id,
        }
    )
    return {'message': 'Logged out successfully'}


@router.get('/auth/oauth/{provider}/authorize')
async def oauth_authorize(
    request: Request,
    response: Response,
    provider: str
):
    state = secrets.token_urlsafe(32)
    state_token = create_oauth_state_token(state, provider)
    response.set_cookie(
        key='oauth_state',
        value=state_token,
        httponly=True,
        samesite='lax',
        max_age=600,
        secure=settings.oauth_state_cookie_secure
    )
    
    auth_url = await auth_service.get_oauth_authorization_url(provider, state)
    
    if not auth_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'OAuth provider {provider} not supported or not configured'
        )
    
    return {'authorization_url': auth_url, 'state': state}


@router.post('/auth/oauth/{provider}/callback')
async def oauth_callback(
    request: Request,
    response: Response,
    provider: str,
    code: str,
    state: str
):
    state_token = request.cookies.get('oauth_state')
    payload = verify_oauth_state_token(state_token) if state_token else None
    if not payload or payload.get('provider') != provider or payload.get('state') != state:
        response.delete_cookie('oauth_state')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid state parameter'
        )
    
    result = await auth_service.authenticate(
        strategy_name=provider,
        request=request,
        code=code
    )
    
    if not result.success:
        raise UnauthorizedException()
    
    tokens = auth_service.create_tokens(
        user_id=result.user_id,
        email=result.user_data.get('email', ''),
        role=result.user_data.get('role', 'user')
    )

    response.delete_cookie('oauth_state')
    
    logger.info(
        f'User authenticated via OAuth: {result.user_id}',
        extra={
            'correlation_id': request.state.correlation_id,
            'user_id': result.user_id,
            'provider': provider,
        }
    )
    
    return TokenResponse(**tokens)
