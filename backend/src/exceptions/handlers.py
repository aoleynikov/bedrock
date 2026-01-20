from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from src.i18n.translator import get_translator


class UnauthorizedException(Exception):
    def __init__(self):
        super().__init__('Unauthorized')


class ForbiddenException(Exception):
    def __init__(self):
        super().__init__('Forbidden')


def format_validation_error(error: dict, translator) -> dict:
    loc = error.get('loc', [])
    field_parts = [str(l) for l in loc if l not in ('body', 'query', 'path')]
    field = '.'.join(field_parts) if field_parts else 'body'
    error_type = error.get('type', '')
    ctx = error.get('ctx', {}) or {}

    msg = translate_validation_message(error_type, ctx, translator)
    
    return {
        'field': field,
        'message': msg,
        'type': error_type
    }


VALIDATION_ERROR_MAP = {
    'missing': ('validation.required', {}),
    'string_too_short': ('validation.string_min_length', {'min_length': 'min_length'}),
    'string_too_long': ('validation.string_max_length', {'max_length': 'max_length'}),
    'value_error.email': ('validation.email_invalid', {}),
    'password_min_length': ('validation.password_min_length', {}),
}


def translate_validation_message(error_type: str, ctx: dict, translator) -> str:
    mapping = VALIDATION_ERROR_MAP.get(error_type)
    if not mapping:
        return translator.t('common.validation_error')

    key, param_map = mapping
    params = {
        param: ctx.get(ctx_key)
        for param, ctx_key in param_map.items()
        if ctx.get(ctx_key) is not None
    }
    return translator.t(key, **params)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    translator = get_translator(request)
    errors = [format_validation_error(error, translator) for error in exc.errors()]
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            'status': translator.t('common.error'),
            'message': translator.t('common.validation_failed'),
            'errors': errors
        }
    )


async def unauthorized_exception_handler(
    request: Request,
    exc: UnauthorizedException
) -> JSONResponse:
    translator = get_translator(request)
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        headers={'WWW-Authenticate': 'Bearer'},
        content={
            'status': translator.t('common.error'),
            'message': translator.t('errors.auth.unauthorized')
        }
    )


async def forbidden_exception_handler(
    request: Request,
    exc: ForbiddenException
) -> JSONResponse:
    translator = get_translator(request)
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            'status': translator.t('common.error'),
            'message': translator.t('errors.auth.forbidden')
        }
    )
