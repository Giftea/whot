import asyncio
import websockets
from websockets.asyncio.client import ClientConnection
from whot import Whot

import json
import secrets


JOIN = {}


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
    event = {
        "type": "player_id",
        "player_id": player_id,
    }

    await websocket.send(json.dumps(event)) 

    while gameConnections.num_of_connections < 2:
        await asyncio.sleep(1)

    game.start_game()

    for i, socket in enumerate(gameConnections.connections, start=1):
        event = {
            "type": "play",
            "player_id": i,
            "game_state": game.view(f"player_{i}")
        }

        await gameConnections.connections[socket].send(json.dumps(event))

    if game.request_mode == True:
        current_player = game.current_player.player_id
        
        event = {
            "type": "request",
            "player_id": 1,
            "game_state": game.view(f"player_1")
        }

        await gameConnections.connections[current_player].send(json.dumps(event))
       
    
    async for message in websocket:
        
        event = json.loads(message)
        
        if event["type"] == "play":           
            if event["player_id"] == game.game_state()["current_player"]:

                card_index = int(event["card"])
                result = game.play(card_index)
                
                if result["status"] == "Success":

                    for i, socket in enumerate(gameConnections.connections, start=1):
                        event = {
                            "type": "play",
                            "player_id": i,
                            "game_state": game.view(f"player_{i}")
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

                    current_player = game.current_player.player_id

                    for i, socket in enumerate(gameConnections.connections, start=1):

                        if socket == current_player:
                            
                            event = {
                                "type": "request",
                                "player_id": i,
                                "game_state": game.view(f"player_{i}")
                            }

                        else:

                            event = {
                                "type": "play",
                                "player_id": i,
                                "game_state": game.view(f"player_{i}")
                            }

                        await gameConnections.connections[socket].send(json.dumps(event))

                elif result['status'] == "GameOver":
                    event = {
                        "type": "win",
                        "winner": result['winner'],
                    }
                    game.save("game.json")
                    websockets.broadcast(gameConnections.connections.values(), json.dumps(event))
            else:
                event = {
                    "type": "message",
                    "message":"It is not your turn" 
                }
                
                await websocket.send(json.dumps(event))

        elif event["type"] == "market":

            if event["player_id"] == game.game_state()["current_player"]:

                game.market()

                for i, socket in enumerate(gameConnections.connections, start=1):
                    event = {
                        "type": "play",
                        "player_id": i,
                        "game_state": game.view(f"player_{i}")
                    }

                    await gameConnections.connections[socket].send(json.dumps(event))

        elif event["type"] == "request":
            suit = event["suit"]

            requester = game.game_state()['current_player']

            card = str(game.request(suit)['requested_suit'])

            for i, socket in enumerate(gameConnections.connections, start=1):

                if socket != requester:
                    event = {
                        "type": "request_card",
                        "message": f"{requester} requested for {card}",
                        "game_state": game.view(f"player_{i}")
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

    join_key = secrets.token_urlsafe(4)
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