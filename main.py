from aiohttp import web
import asyncio
from websockets.asyncio.server import serve
from server import handler

PORT = 8000
WEBSOCKET_PORT = 8765

# Serve index.html
async def handle_index(request):
    return web.FileResponse("index.html")

# WebSocket server function
async def websocket_server():
    async with serve(handler, "0.0.0.0", WEBSOCKET_PORT):
        print(f"WebSocket server running at ws://0.0.0.0:{WEBSOCKET_PORT}")
        await asyncio.Future()  # Keep the WebSocket server running

# Create an aiohttp web app
app = web.Application()
app.router.add_get("/", handle_index)
app.router.add_static("/", path=".", name="static")

# Function to run the aiohttp server
async def run_server():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    print(f"HTTP server running at http://0.0.0.0:{PORT}")
    await site.start()
    await asyncio.Future()  # Keep running

# Run both WebSocket and HTTP server concurrently
async def main():
    await asyncio.gather(websocket_server(), run_server())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server shut down by user.")
