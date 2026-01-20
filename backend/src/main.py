import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_client import make_asgi_app
from src.config import settings
from src.database.connection import DatabaseConnection
from src.exceptions import (
    validation_exception_handler,
    unauthorized_exception_handler,
    forbidden_exception_handler,
    UnauthorizedException,
    ForbiddenException
)
from src.middleware.correlation import CorrelationMiddleware
from src.logging.logger import get_logger
from src.i18n.translator import get_translator
from src.routes import api
from src.routes import users
from src.routes import tasks
from src.routes import logs
from src.routes import auth
from src.routes import files
from src.tasks.queue import enqueue
from pathlib import Path

logger = get_logger(__name__)

metrics_app = make_asgi_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await DatabaseConnection.connect()
    logger.info('Connected to MongoDB')
    max_attempts = 10
    enqueued = False
    for attempt in range(1, max_attempts + 1):
        try:
            enqueue('startup_tasks')
            logger.info('Startup tasks enqueued', extra={'attempt': attempt})
            enqueued = True
            break
        except Exception as error:
            logger.error(
                'Failed to enqueue startup tasks',
                extra={'error': error, 'attempt': attempt}
            )
            if attempt == max_attempts:
                raise RuntimeError('Failed to enqueue startup tasks') from error
            await asyncio.sleep(2)
    if not enqueued:
        raise RuntimeError('Failed to enqueue startup tasks')
    yield
    await DatabaseConnection.disconnect()
    logger.info('Disconnected from MongoDB')


app = FastAPI(
    title='Bedrock API',
    description='FastAPI backend with MongoDB',
    version='1.0.0',
    lifespan=lifespan
)

app.add_middleware(CorrelationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(UnauthorizedException, unauthorized_exception_handler)
app.add_exception_handler(ForbiddenException, forbidden_exception_handler)

app.mount('/metrics', metrics_app)

# Mount static files for local storage (only if using local storage)
if settings.file_storage_type == 'local':
    storage_path = Path(settings.file_storage_path)
    storage_path.mkdir(parents=True, exist_ok=True)
    app.mount('/storage', StaticFiles(directory=str(storage_path)), name='storage')

app.include_router(api.router, prefix='/api', tags=['api'])
app.include_router(auth.router, prefix='/api', tags=['auth'])
app.include_router(users.router, prefix='/api', tags=['users'])
app.include_router(files.router, prefix='/api', tags=['files'])
app.include_router(tasks.router, prefix='/api', tags=['tasks'])
app.include_router(logs.router, prefix='/api', tags=['logs'])


@app.get('/')
async def root(request: Request):
    translator = get_translator(request)
    return {'message': translator.t('messages.welcome')}
