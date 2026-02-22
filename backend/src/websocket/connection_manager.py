from typing import Any

from starlette.websockets import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}

    def register(self, websocket: WebSocket, user_id: str) -> None:
        if user_id not in self._connections:
            self._connections[user_id] = set()
        self._connections[user_id].add(websocket)

    def unregister(self, websocket: WebSocket) -> None:
        for user_id, conns in list(self._connections.items()):
            conns.discard(websocket)
            if not conns:
                del self._connections[user_id]

    async def send_to_user(self, user_id: str, data: Any) -> None:
        conns = self._connections.get(user_id)
        if not conns:
            return
        dead = []
        for ws in list(conns):
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.unregister(ws)

    async def broadcast(self, data: Any) -> None:
        dead = []
        for conns in list(self._connections.values()):
            for ws in list(conns):
                try:
                    await ws.send_json(data)
                except Exception:
                    dead.append(ws)
        for ws in dead:
            self.unregister(ws)


connection_manager = ConnectionManager()
