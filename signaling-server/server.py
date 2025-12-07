#!/usr/bin/env python3
# Простой WebSocket сигнальный сервер для WiFi Talker
# Запуск: python server.py

import asyncio
import json
import logging
from urllib.parse import urlparse, parse_qs
import websockets
from websockets.exceptions import ConnectionClosed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Словарь для хранения комнат: roomId -> set of websocket connections
rooms = {}

async def handle_client(websocket):
    """Обработка подключения клиента"""
    try:
        # Парсим URL: /roomId?initiator=true
        parsed = urlparse(websocket.path)
        room_id = parsed.path.lstrip('/')
        query_params = parse_qs(parsed.query)
        is_initiator = query_params.get('initiator', ['false'])[0] == 'true'
        
        logger.info(f"Новое подключение: комната={room_id}, инициатор={is_initiator}")
        
        if not room_id:
            await websocket.close(code=1008, reason="Room ID required")
            return
        
        # Добавляем в комнату
        if room_id not in rooms:
            rooms[room_id] = set()
        rooms[room_id].add(websocket)
        
        # Отправляем сообщение о подключении
        await websocket.send(json.dumps({"type": "connected", "roomId": room_id}))
        
        # Если это второй пользователь в комнате, уведомляем первого
        if len(rooms[room_id]) == 2 and is_initiator:
            for client in rooms[room_id]:
                if client != websocket:
                    try:
                        await client.send(json.dumps({"type": "peer-ready"}))
                    except:
                        pass
        
        # Обработка сообщений
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Сообщение в комнате {room_id}: {data.get('type', 'unknown')}")
                
                # Пересылаем сообщение всем остальным в комнате
                for client in rooms[room_id]:
                    if client != websocket:
                        try:
                            await client.send(message)
                        except:
                            pass
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка обработки сообщения: {e}")
    except ConnectionClosed:
        pass
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    finally:
        # Удаляем из комнаты при отключении
        if room_id in rooms:
            rooms[room_id].discard(websocket)
            if len(rooms[room_id]) == 0:
                del rooms[room_id]
                logger.info(f"Комната {room_id} удалена")
            else:
                logger.info(f"Отключение из комнаты {room_id}")

async def main():
    """Запуск сервера"""
    PORT = 8080
    logger.info(f"Сигнальный сервер запущен на порту {PORT}")
    logger.info(f"Подключение: ws://localhost:{PORT}/<room-id>")
    
    async with websockets.serve(handle_client, "0.0.0.0", PORT):
        await asyncio.Future()  # Запускаем бесконечно

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Сервер остановлен")

