import asyncio
import websockets

async def message_handler(websocket):
    while True:
        message = input("Enter message: ")
        await websocket.send(message)
        
        # Отримання відповіді від сервера
        response = await websocket.recv()
        print(f"Server response: {response}")

async def ping_handler(websocket):
    while True:
        await websocket.ping()
        await asyncio.sleep(5)
        
async def main():
    uri = "ws://localhost:8765"  # Адреса вашого WebSocket сервера
    async with websockets.connect(uri) as websocket:
           
        # Основна логіка обробки повідомлень
        message_task = asyncio.create_task(message_handler(websocket))

        # Очікування завершення обох задач
        await asyncio.gather(message_task)

if __name__ == "__main__":
    asyncio.run(main())

