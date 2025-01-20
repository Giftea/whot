function initGame(websocket) {
    websocket.addEventListener("open", () => {
        // Send an "init" event according to who is connecting.
        const params = new URLSearchParams(window.location.search);
        let event = { type: "init" };
        if (params.has("join")) {
            // Second player joins an existing game.
            event.join = params.get("join");
        } else if (params.has("watch")) {
            // Spectator watches an existing game.
            event.watch = params.get("watch");
        } else {
            // First player starts a new game.
        }
        websocket.send(JSON.stringify(event));
    });
}

function receiveMoves(websocket) {
    const current_player = document.getElementById("current_player");
    const pile_top = document.getElementById("pile_top");
    const player_one = document.getElementById("player_one");
    const player_two = document.getElementById("player_two");

    websocket.addEventListener("message", ({ data }) => {
        console.log(data)
        const event = JSON.parse(data);

        

        switch (event.type) {
            case "init":
                // Create links for inviting the second player and spectators.
                document.querySelector(".join").href = "?join=" + event.join;
                //document.querySelector(".watch").href = "?watch=" + event.watch;
                break;

            case "play":
                current_player.textContent = `Current Player: ${event.game_state["current_player"]}`
                pile_top.textContent = `Pile top: ${event.game_state["pile_top"]}`
                player_one.textContent = `Player One: ${event.game_state["player_1"]}`
                player_two.textContent = `Player Two: ${event.game_state["player_2"]}`
                break;

            case "win":
                showMessage(`Player ${event.player} wins!`);
                // No further messages are expected; close the WebSocket connection.
                websocket.close(1000);
                break;

            case "error":
                showMessage(event.message);
                break;

            default:
                throw new Error(`Unsupported event type: ${event.type}.`);
        }
    });
}

function showMessage(message) {
    window.setTimeout(() => window.alert(message), 50);
}

function sendMoves(websocket, card, playBtn, marketBtn) {
    // Don't send moves for a spectator watching a game.
    const params = new URLSearchParams(window.location.search);
    if (params.has("watch")) {
        return;
    }

    // When clicking a column, send a "play" event for a move in that column.
    playBtn.addEventListener("click", () => {

        if (card.value) {
            console.log(card.value)

            const event = {
                type: "play",
                card: card.value,
            };
            websocket.send(JSON.stringify(event));
        }
    });

    // When clicking a column, send a "play" event for a move in that column.
    marketBtn.addEventListener("click", () => {
        const event = {
            type: "market",
        };
        websocket.send(JSON.stringify(event));

    });
}

window.addEventListener("DOMContentLoaded", () => {
    // Open the WebSocket connection and register event handlers.
    const card = document.getElementById("card");
    const playBtn = document.getElementById("play");
    const marketBtn = document.getElementById("market");

    const websocket = new WebSocket("ws://localhost:8765/");
    initGame(websocket);
    receiveMoves(websocket);
    sendMoves(websocket, card, playBtn, marketBtn);
});
