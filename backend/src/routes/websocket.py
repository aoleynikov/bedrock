from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from src.auth.service import auth_service
from src.repositories import get_user_repository
from src.repositories.user_repository import UserRepository
from src.websocket.connection_manager import connection_manager

router = APIRouter()


@router.websocket('/ws')
async def websocket_endpoint(
    websocket: WebSocket,
    repo: UserRepository = Depends(get_user_repository)
):
    token = websocket.query_params.get('token')
    if not token:
        await websocket.close(code=4401)
        return
    payload = auth_service.verify_access_token(token)
    if not payload:
        await websocket.close(code=4401)
        return
    user_id = payload.get('sub')
    if not user_id:
        await websocket.close(code=4401)
        return
    user = await repo.get_by_id(user_id)
    if not user:
        await websocket.close(code=4401)
        return
    await websocket.accept()
    connection_manager.register(websocket, user.id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        connection_manager.unregister(websocket)
