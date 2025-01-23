import asyncio
import websockets
from websockets.asyncio.server import serve
from websockets.asyncio.client import ClientConnection

from whot import Whot

import json
import secrets


JOIN = {}

def serialize_game_state(game_state: dict, player_id: str):
    state = game_state.copy()

    state['pile_top'] = str(state['pile_top'])

    current_player = player_id
    keys: list[str] = state.keys()

    for key in keys:
        if key.startswith("player_"):
            if key == current_player:
                state[key] = [str(card) for card in state[key]]
            else:
                state[key] = len(state[key])

    return state

class GameConnection:
    """
    This class stores the created instance of the game
    it's connections
    The number of players that have joined    
    """

    def __init__(self, game: Whot):
        self.game = game
        self.connections: dict[str, ClientConnection] = {}
        self.num_of_connections = 0
    
    def add_connection(self, connection: ClientConnection):
        if self.game.num_of_players != self.num_of_connections:
            self.num_of_connections += 1
            self.connections[f"player_{self.num_of_connections}"] = connection
            return f"player_{self.num_of_connections}"
        else:
            return False

async def play(websocket: ClientConnection, game: Whot, player_id: str, gameConnections: GameConnection):
    
    while gameConnections.num_of_connections < 2:
        await asyncio.sleep(1)

    for i, socket in enumerate(gameConnections.connections, start=1):
        event = {
            "type": "play",
            "player_id": i,
            "game_state": serialize_game_state(game.game_state(), f"player_{i}")
        }

        await gameConnections.connections[socket].send(json.dumps(event))
    
    async for message in websocket:
        
        event = json.loads(message)
        
        if event["type"] == "play":
            card_index = int(event["card"])
            print("Card Index:", card_index)
            result = game.play(card_index)
            
            if result["status"] == "Played":

                for i, socket in enumerate(gameConnections.connections, start=1):
                    event = {
                        "type": "play",
                        "player_id": i,
                        "game_state": serialize_game_state(game.game_state(), f"player_{i}")
                    }

                    await gameConnections.connections[socket].send(json.dumps(event))
            
            elif result["status"] == "Failed":
                 
                 for i, socket in enumerate(gameConnections.connections, start=1):
                    event = {
                        "type": "failed",
                        "current_player": game.game_state()["current_player"]
                   }

                    await gameConnections.connections[socket].send(json.dumps(event))

            elif result['status'] == "Request":

                # event = {
                #     "type": "request",
                #     "current_player": game.game_state()["current_player"],
                # }

                # await gameConnections.connections[game.game_state()["current_player"]].send(json.dumps(event)) 

                for i, socket in enumerate(gameConnections.connections, start=1):
                    event = {
                        "type": "request",
                        "player_id": i,
                        "game_state": serialize_game_state(game.game_state(), f"player_{i}")
                    }

                    await gameConnections.connections[socket].send(json.dumps(event))                            

            elif result['status'] == "GameOver":
                event = {
                    "type": "win",
                    "winner": result['winner'],
                }
                websockets.broadcast(gameConnections.connections.values(), json.dumps(event))
        
        elif event["type"] == "market":

            game.market()

            for i, socket in enumerate(gameConnections.connections, start=1):
                event = {
                    "type": "play",
                    "player_id": i,
                    "game_state": serialize_game_state(game.game_state(), f"player_{i}")
                }

                await gameConnections.connections[socket].send(json.dumps(event))

        elif event["type"] == "request":
            suit = int(event["suit"])

            requester = game.game_state()['current_player']

            card = str(game.request(suit)['requested_suit'])

            for i, socket in enumerate(gameConnections.connections, start=1):
                event = {
                    "type": "request_card",
                    "message": f"{requester} requested for {card}",
                    "game_state": serialize_game_state(game.game_state(), f"player_{i}")
                }

                await gameConnections.connections[socket].send(json.dumps(event))



async def join(websocket: ClientConnection, join_key):
    try:
        gameConnection: GameConnection = JOIN[join_key]
        print("Joined")
    except KeyError:
        print("Game doesn't exist")
        return

    player_id = gameConnection.add_connection(websocket)

    await play(websocket, gameConnection.game, player_id, gameConnection)

async def start(websocket: ClientConnection):
    game = Whot(2, number_of_cards=4)
    gameConnection = GameConnection(game)
    player_id = gameConnection.add_connection(websocket)

    join_key = secrets.token_urlsafe(12)
    JOIN[join_key] = gameConnection

    try:
        event = {
            "type": "init",
            "join": join_key
        }

        await websocket.send(json.dumps(event))
        await play(websocket, game, player_id, gameConnection)
    finally:
        del JOIN[join_key]

async def handler(websocket: ClientConnection):

    message = await websocket.recv()
    event = json.loads(message)
    assert event["type"] == "init"
    if "join" in event:
        await join(websocket, event["join"])
    else:
        await start(websocket)

async def main():
    async with serve(handler, "localhost", 8765):
        print("Server running on: localhost:8765")
        await asyncio.get_running_loop().create_future()  # run forever

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server shut down by user.")