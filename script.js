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

function addMiddleCardImage(text) {
    const cardImg = document.getElementById("card_top");

    const card = text.toLowerCase().split(" ");

    let path;

    if (card[1] != 'whot') {
        path = `assets/images/${card[1]}/${card[0]}_${card[1]}.png`
    } else {
        path = `assets/images/20_whot.png`
    }
    cardImg.src = path;
}

function addOponnentCardImages(num_cards) {
    const opponent_cards = document.getElementById("opponent_cards");

    // Remove all children
    opponent_cards.replaceChildren();

    for (let i = 0; i < num_cards; i++) {
        // Create a new image element
        const newCard = document.createElement('img');

        // Set attributes for the image
        newCard.src = 'assets/images/whot_back.png'; // Path to the image
        newCard.alt = 'Opponent Card'; // Alternative text
        newCard.width = 100; // Set width
        newCard.height = 120; // Set height

        // Append the new image to the opponent_cards div
        opponent_cards.appendChild(newCard);
    }
}

function addPlayerCardImages(cards, websocket) {
    const player_cards = document.getElementById("player_cards");

    // Remove all children
    player_cards.replaceChildren();

    for (let i = 0; i < cards.length; i++) {
        // Create a new image element
        const newCard = document.createElement('img');

        const card = cards[i].toLowerCase().split(" ");

        // Set attributes for the image
        if (card[1] != 'whot') {
            newCard.src = `assets/images/${card[1]}/${card[0]}_${card[1]}.png`; // Path to the image
        } else {
            newCard.src = `assets/images/20_whot.png`
        }
        newCard.alt = 'Player Card'; // Alternative text
        newCard.width = 100; // Set width
        newCard.height = 120; // Set height
        console.log('Card: ', card[0])
        newCard.onclick = () => {
            const event = {
                type: "play",
                card: i,
            };
            websocket.send(JSON.stringify(event));
        }

        // Append the new image to the opponent_cards div
        player_cards.appendChild(newCard);
    }
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

                const opponent = Object.keys(event.game_state).filter(key => key.startsWith('player_')).filter(key => key !== `player_${event.player_id}`)

                addMiddleCardImage(event.game_state["pile_top"])
                addOponnentCardImages(event.game_state[opponent])
                addPlayerCardImages(event.game_state[`player_${event.player_id}`], websocket)
                break;
            
            case "request":
                current_player.textContent = `Current Player: ${event.game_state["current_player"]}`

                const opponent2 = Object.keys(event.game_state).filter(key => key.startsWith('player_')).filter(key => key !== `player_${event.player_id}`)

                let div = document.getElementById("i_need");

                addMiddleCardImage(event.game_state["pile_top"])
                addOponnentCardImages(event.game_state[opponent2])
                addPlayerCardImages(event.game_state[`player_${event.player_id}`], websocket)

                div.style.visibility = "visible";

                break;
            
            case "request_card":
                current_player.textContent = `Current Player: ${event.game_state["current_player"]}`
                let div2 = document.getElementById("i_need");
                div2.style.visibility = "hidden";
                console.log(event.message)
                break;


            case "win":
                showMessage(`Player ${event.winner} wins!`);
                // No further messages are expected; close the WebSocket connection.
                websocket.close(1000);
                break;
            
            case "failed":
                console.log(`${event.current_player} failed`)
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

function sendMoves(websocket, card, playBtn) {
    // Don't send moves for a spectator watching a game.
    const params = new URLSearchParams(window.location.search);
    if (params.has("watch")) {
        return;
    }
    console.log("Send moves")
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
    // marketBtn.addEventListener("click", () => {
    //     const event = {
    //         type: "market",
    //     };
    //     console.log("Market!!")
    //     websocket.send(JSON.stringify(event));

    // });
}



window.addEventListener("DOMContentLoaded", () => {
    // Open the WebSocket connection and register event handlers.
    const card = document.getElementById("card");
    // const playBtn = document.getElementById("play");
    const market = document.getElementById("market");
    const requestBtn = document.getElementById("requestBtn");
    const requestCard = document.getElementById("request");

    console.log(requestCard)
    
    const websocket = new WebSocket("ws://localhost:8765/");

    initGame(websocket);
    receiveMoves(websocket);
    // sendMoves(websocket, card, playBtn);


    market.onclick = () => {
        const event = {
            type: "market",
        };
        console.log("Market!!")
        websocket.send(JSON.stringify(event));        
    }

    requestBtn.onclick = () => {
        if (requestCard.value ) {
            const event = {
                type: "request",
                suit: requestCard.value
            };
            console.log("Request!!")
            websocket.send(JSON.stringify(event));
        }
    }
});