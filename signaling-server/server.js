// Простой WebSocket сигнальный сервер для WiFi Talker
// Запуск: node server.js

const WebSocket = require('ws');
const http = require('http');

const server = http.createServer();
const wss = new WebSocket.Server({ server });

const rooms = new Map(); // roomId -> Set of WebSocket connections

wss.on('connection', (ws, req) => {
    const url = new URL(req.url, `http://${req.headers.host}`);
    const roomId = url.pathname.substring(1); // Убираем первый /
    const isInitiator = url.searchParams.get('initiator') === 'true';
    
    console.log(`Новое подключение: комната=${roomId}, инициатор=${isInitiator}`);
    
    if (!roomId) {
        ws.close(1008, 'Room ID required');
        return;
    }
    
    // Добавляем в комнату
    if (!rooms.has(roomId)) {
        rooms.set(roomId, new Set());
    }
    const room = rooms.get(roomId);
    room.add(ws);
    
    // Отправляем сообщение о подключении
    ws.send(JSON.stringify({ type: 'connected', roomId }));
    
    // Если это второй пользователь в комнате, уведомляем первого
    if (room.size === 2 && isInitiator) {
        // Уведомляем другого пользователя, что можно начинать
        room.forEach(client => {
            if (client !== ws && client.readyState === WebSocket.OPEN) {
                client.send(JSON.stringify({ type: 'peer-ready' }));
            }
        });
    }
    
    // Обработка сообщений
    ws.on('message', (message) => {
        try {
            const data = JSON.parse(message.toString());
            console.log(`Сообщение в комнате ${roomId}:`, data.type);
            
            // Пересылаем сообщение всем остальным в комнате
            room.forEach(client => {
                if (client !== ws && client.readyState === WebSocket.OPEN) {
                    client.send(message.toString());
                }
            });
        } catch (e) {
            console.error('Ошибка обработки сообщения:', e);
        }
    });
    
    // Обработка отключения
    ws.on('close', () => {
        console.log(`Отключение из комнаты ${roomId}`);
        room.delete(ws);
        if (room.size === 0) {
            rooms.delete(roomId);
            console.log(`Комната ${roomId} удалена`);
        }
    });
    
    ws.on('error', (error) => {
        console.error('WebSocket error:', error);
    });
});

const PORT = process.env.PORT || 8080;
server.listen(PORT, '0.0.0.0', () => {
    console.log(`Сигнальный сервер запущен на порту ${PORT}`);
    console.log(`Подключение: ws://localhost:${PORT}/<room-id>`);
});

