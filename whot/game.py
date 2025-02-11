from .deck import Deck, Card, Suit
from .player import Player
import json
import uuid
import os

from enum import Enum

# Event source note:
# The store eve

def serialize_game_state(game_state: dict):
    state = game_state.copy()

    state['pile_top'] = str(state['pile_top'])
    keys: list[str] = state.keys()

    for key in keys:
        if key.startswith("player_"):
                state[key] = [str(card) for card in state[key]]

    return state

def event_storage(func):
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        event = serialize_game_state(self.game_state())
        if len(self.event_store) >=  1:
            if self.event_store[-1] == event:
                return result
            self.event_store.append(event)  
            return result
    return wrapper


class Whot:
    # Whot Engine

    def __init__(self, number_of_players: int = 2, number_of_cards: int = 4):
        """
        This would be used to configure the whot engine.
        """

        self.num_of_players = number_of_players
        self.num_of_cards = number_of_cards
        self.event_store = []

    
    def test_mode(self, test_pile_card: Card, test_player_cards: list[Card]):
        """
        In test mode you can set the top pile, players card, opponents
        set top pile
        select the suit name and number of card for both players and opponents
        Let's simpl
        """
        deck = Deck()
        deck.shuffle()

        # create test pile
        self.pile: list[Card] = []
        self.pile.append(deck.draw_card(test_pile_card))

        # Create test player 
        self.players: list[Player] = []
        self.players.append(Player("player_1"))

        self.players[0].recieve(deck.draw_cards(test_player_cards))
        
        for i in range(1, self.num_of_players):
            self.players.append(Player(f"player_{i + 1}"))

        for p in self.players[1:]:
            p.recieve(deck.deal_card(self.num_of_cards))       

        
        self.gen: Deck = deck
        self.current_player: Player = self.players[0]
        self.game_running = True
        self.request_mode = False
        self.requested_suit = None

        self.initial_play_state = False
        
        self.event_store.append(serialize_game_state(self.game_state()))

    def game_mode(self):
        # Create deck and shuffle
        deck = Deck()
        deck.shuffle()

        # Create players
        self.players: list[Player] = []
        for i in range(self.num_of_players):
            self.players.append(Player(f"player_{i + 1}"))
        
        for p in self.players:
            p.recieve(deck.deal_card(self.num_of_cards))
        
        self.pile: list[Card] = deck.deal_card(1)
        self.gen: Deck = deck
        self.current_player: Player = self.players[0]
        self.game_running = True
        self.request_mode = False
        self.requested_suit = None

        self.initial_play_state = False

        self.event_store.append(serialize_game_state(self.game_state()))
    
    
    def view(self, player_id):
        """
        Get a view of the game from a player's perspective
        """
        view = {}

        view["current_player"] = self.current_player.player_id
        view["pile_top"] = str(self.pile[-1])

        for p in self.players:
            if (p.player_id == player_id):
                view[p.player_id] = [ str(card) for card in p._cards ]
            else:
                view[p.player_id] = len(p._cards)

        return view
    
    # @property
    # def num_of_players(self):
    #     """
    #     Get the number of players in the game
    #     """

    #     return len(self.players)
    
    def game_state(self):
        self.current_state = { "current_player": self.current_player.player_id }
        self.current_state["pile_top"] = self.pile[-1]

        for p in self.players:
            self.current_state[p.player_id] = p._cards
        
        return self.current_state

    @event_storage
    def start_game(self):

        if self.initial_play_state == False:
            self.initial_play_state = True

            if self.pile[0].face == 2:
                self.handle_pick_two(self.current_player)
                self.next_player()

            if self.pile[0].face == 8:
                self.next_player()
            
            if self.pile[0].face == 14:
                self.handle_go_gen()
            
            if self.pile[0].face == 20:
                self.request_mode = True

    @event_storage
    def play(self, card_index: int):

        selected_card: Card = self.current_state[self.current_player.player_id][card_index]
        top_card = self.pile[-1]

        if (selected_card.suit == Suit.WHOT):
            self.pile.append(selected_card)
            self.current_player._cards.remove(selected_card)

            if (len(self.current_player._cards) == 0):
                return {"status": "GameOver", "winner":self.current_player.player_id }
            
            return {"status": "Request"}

        if self.request_mode:
            # Hold on logic in request mode
            if (selected_card.suit == self.requested_suit and selected_card.face == 1):
                self.pile.append(selected_card)
                self.current_player._cards.remove(selected_card)
                if (len(self.current_player._cards) == 0):
                    return {"status": "GameOver", "winner":self.current_player.player_id }
                self.request_mode = False
                return {"status": "Played"}

            # Go to market logic
            if selected_card.suit == self.requested_suit and selected_card.face == 14:
                self.pile.append(selected_card)
                self.current_player._cards.remove(selected_card)

                self.handle_go_gen(self.current_player)

                if (len(self.current_player._cards) == 0):
                    return {"status": "GameOver", "winner":self.current_player.player_id }
                
                self.next_player()
                self.next_player()
                self.request_mode = False
                return {"status": "Played"}

            # Suspension logic
            if selected_card.suit == self.requested_suit and selected_card.face == 8:
                self.pile.append(selected_card)
                self.current_player._cards.remove(selected_card)
            
                if (len(self.current_player._cards) == 0):
                    return {"status": "GameOver", "winner":self.current_player.player_id }
                
                self.next_player()
                self.next_player()
                return {"status": "Played"}

            # whot card logic
            if selected_card.suit == self.requested_suit:
                self.pile.append(selected_card)
                self.current_player._cards.remove(selected_card)

                if (len(self.current_player._cards) == 0):
                    return {"status": "GameOver", "winner":self.current_player.player_id }
                
                self.next_player()
                self.request_mode = False
                return {"status": "Played"}              

            else:
                return {"status": "Failed"}
        
        # Hold on logic
        if (selected_card.face == 1 and selected_card.suit == top_card.suit) or (selected_card.face == 1 and top_card.face == 1):
            print("Hold on!")
            self.pile.append(selected_card)
            self.current_player._cards.remove(selected_card)
            if (len(self.current_player._cards) == 0):
                return {"status": "GameOver", "winner":self.current_player.player_id }
            return {"status": "Played"}
        
        # Go to market logic
        if (selected_card.face == 14 and selected_card.suit == top_card.suit) or (selected_card.face == 14 and top_card.face == 14):
            self.pile.append(selected_card)
            self.current_player._cards.remove(selected_card)
            self.handle_go_gen(self.current_player)

            if (len(self.current_player._cards) == 0):
                return {"status": "GameOver", "winner":self.current_player.player_id }
            
            self.next_player()
            self.next_player()
            return {"status": "Played"}
        
        # Suspension logic
        if (selected_card.face == 8 and selected_card.suit == top_card.suit) or (selected_card.face == 8 and top_card.face == 8):
            self.pile.append(selected_card)
            self.current_player._cards.remove(selected_card)
            
            if (len(self.current_player._cards) == 0):
                return {"status": "GameOver", "winner":self.current_player.player_id }
            
            self.next_player()
            self.next_player()
            return {"status": "Played"}
        
        # Pick two logic
        if (selected_card.face == 2 and selected_card.suit == top_card.suit) or (selected_card.face == 2 and top_card.face == 2):
            self.pile.append(selected_card)
            self.current_player._cards.remove(selected_card)
            self.handle_pick_two(self.get_next_player())
            
            if (len(self.current_player._cards) == 0):
                return {"status": "GameOver", "winner":self.current_player.player_id }
            
            self.next_player()
            self.next_player()
            return {"status": "Played"}                     

        if (selected_card.face == top_card.face or selected_card.suit == top_card.suit ):
            self.pile.append(selected_card)
            self.current_player._cards.remove(selected_card)

            if (len(self.current_player._cards) == 0):
                return {"status": "GameOver", "winner":self.current_player.player_id }
                        
            self.next_player()
            return {"status": "Played"}
        else:
            return {"status": "Failed"}
            # print("Couldn't play successfully")

        # print(selected_card)
    
    @event_storage
    def market(self):
        
        if self.gen.cards == []:
            new_cards = self.pile[:-1]
            self.pile = self.pile[-1:]
            self.gen.receive_cards(new_cards)

        recieved_card = self.gen.deal_card(1)
        self.current_player.recieve(recieved_card)
        self.next_player()

    def request(self, suit):

        self.request_mode = True

        if suit == "whot":
            pass
        else:
            try:
                self.requested_suit = Suit(suit)
                self.next_player()
                return {"requested_suit": self.requested_suit}
            except ValueError:
                # Handle the case where card_index doesn't match any Suit
                pass
    
    def next_player(self, skip=1):

        n = self.players.index(self.current_player)
        try:
            self.current_player = self.players[n + skip]
        except IndexError:
            self.current_player = self.players[0]

    def get_next_player(self):
        n = self.players.index(self.current_player)
        try:
            return self.players[n + 1]
        except IndexError:
            return self.players[0]
    
    def handle_go_gen(self, exempt_player: Player | None = None):
        """
        Method to handle going gen
        """

        # current_player = self.current_player
        
        if exempt_player:
            gen_list = self.players.copy()
            gen_list.remove(exempt_player)
        
            print(f"All players except {exempt_player} Go Gen: ")
            for player in gen_list:
                recieved_card = self.gen.deal_card(1)
                player.recieve(recieved_card)
                print(f"{player} you recieved: {recieved_card}")

        else:
            print(f"Everyone Go Gen: ")
            for player in self.players:
                recieved_card = self.gen.deal_card(1)
                player.recieve(recieved_card)
                print(f"{player} you recieved: {recieved_card}")
    
    def handle_pick_two(self, player: Player | list[Player]):
        """
        Method to handle giving players pick two
        """
        # get_next_player = self.get_next_player()

        print(f"{player} Pick two: ")
        recieved_card = self.gen.deal_card(2)
        player.recieve(recieved_card)
        print(f"{player} you recieved: {recieved_card}")
    
    def save(self, path):
        """
        Appends a new game event to the JSON file while preserving existing data.
        """

        game = {
            "id": str(uuid.uuid4()),
            "moves": self.event_store
        }

        # Check if file exists and has content
        if os.path.exists(path) and os.path.getsize(path) > 0:
            with open(path, "r") as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, list):
                        data = [data]  # Convert old format to list
                except json.JSONDecodeError:
                    data = []
        else:
            data = []

        data.append(game)  # Append new game

        with open(path, "w") as f:
            json.dump(data, f, indent=4)  # Pretty-print JSON for readability

        return True



# Old Engine

# class Game:
#     """
#     A game has:
#     1. A deck of cards.
#     2. Two players(currently) with pile of six cards each.
#     3. A General market
#     4. A pile
#     5. A instance variable keeping track of turns
#     6. Rules defining the game of whots
#     """

#     def __init__(self, deck: Deck, players: list[Player]):
#         deck.shuffle()
#         self.players: list[Player] = players
#         for p in self.players:
#             p.recieve(deck.deal_card(3))
#         self.pile: list[Card] = deck.deal_card(1)
#         self.gen: Deck = deck
#         self.current_player: Player = self.players[0]

#     def play(self):
#         self.initial_process()
#         while True:
#             print(f"Pile: {self.pile[-1]}")
#             print(f"{self.current_player.player_id}: {self.current_player._cards}")
#             print()
#             inp = int(input("Please input card index or -1 to go gen: "))
#             if inp == -1:
#                 self.current_player.recieve(self.gen.deal_card(1))
#             else:
#                 try:
#                     if (
#                         self.current_player._cards[inp].same(self.pile[-1])
#                         or self.current_player._cards[inp].suit == Suit.WHOT
#                     ):
#                         self.pile.append(self.current_player._cards[inp])
#                         self.current_player._cards.remove(
#                             self.current_player._cards[inp]
#                         )

#                         self.process()

#                     else:
#                         print("Card doesn't match top of pile")
#                         self.next_player()

#                 except IndexError:
#                     print("You are out of order. Try again")
#                     self.next_player()

#             if self.check_winner():
#                 break

#             self.next_player()

#         print(f"{self.current_player} you win.")

#     def initial_process(self):
#         """
#         This method handles what will happen to the initial player
#         If the card on the top of the file is a special one.
#         """

#         current_player = self.current_player
#         next_player = self.get_next_player()

#         if self.pile[-1].face == 2:
#             # The current player should pick two
#             self.handle_pick_two(current_player)

#         if self.pile[-1].face == 14:
#             # All players should go gen
#             self.handle_go_gen()

#         if self.pile[-1].face == 8:
#             # The current player should be suspended
#             self.handle_suspension(current_player)
    
#         if self.pile[-1].face == 1:
#             # The current player can play any card of their choice
#             self.handle_hold_on(next_player)

#         if self.pile[-1] == Card(Suit.WHOT, 20):
#             self.handle_whot(next_player)

#         return

#     def process(self):
#         """
#         This method handles what will happen during the normal game process
#         """

#         current_player = self.current_player
#         next_player = self.get_next_player()
        
#         if self.pile[-1].face == 2:
#             # The next player should pick two cards
#             self.handle_pick_two(next_player)

#         if self.pile[-1].face == 14:
#             # All players should go gen except the current player
#             self.handle_go_gen(current_player)

#         if self.pile[-1].face == 8:
#             # Suspend the next player
#             self.handle_suspension(next_player)

#         if self.pile[-1].face == 1:
#             # The next player should hold on for the current player
#             self.handle_hold_on(next_player)

#         if self.pile[-1] == Card(Suit.WHOT, 20):
#             # The next player should give the current player any card of their choice 
#             self.handle_whot(next_player)
        
#         return
    
#     def handle_pick_two(self, player: Player):
#         """
#         Method to handle giving players pick two
#         """
#         # get_next_player = self.get_next_player()

#         print(f"{player} Pick two: ")
#         recieved_card = self.gen.deal_card(2)
#         player.recieve(recieved_card)
#         print(f"{player} you recieved: {recieved_card}")

#     def handle_go_gen(self, exempt_player: Player | None = None):
#         """
#         Method to handle going gen
#         """

#         # current_player = self.current_player
        
#         if exempt_player:
#             gen_list = self.players.copy()
#             gen_list.remove(exempt_player)
        
#             print(f"All players except {exempt_player} Go Gen: ")
#             for player in gen_list:
#                 recieved_card = self.gen.deal_card(1)
#                 player.recieve(recieved_card)
#                 print(f"{player} you recieved: {recieved_card}")

#         else:
#             print(f"Everyone Go Gen: ")
#             for player in self.players:
#                 recieved_card = self.gen.deal_card(1)
#                 player.recieve(recieved_card)
#                 print(f"{player} you recieved: {recieved_card}")


#     def handle_suspension(self, player: Player):
#         """
#         Method to handle suspension for a particular player
#         """

#         print(f"{player} has been suspended: ")
#         self.next_player()
    
#     def handle_hold_on(self, player: Player):
#         """
#         Method to handle hold on
#         """

#         print(f"{player} Hold on: ")
#         print(f"{self.current_player._cards}")
#         inp = int(
#             input(f"{self.current_player} Please input any card index of your choice: ")
#         )
#         self.pile.append(self.current_player._cards[inp])
#         self.current_player._cards.remove(self.current_player._cards[inp])
#         if self.pile[-1].face == 1:
#             self.handle_hold_on(player)
#         if self.pile[-1].face == 14:
#             self.handle_go_gen(self.current_player)
#         if self.pile[-1].face == 8:
#             self.handle_suspension(player)
#             return
#         if self.pile[-1].face == 2:
#             self.handle_pick_two(player)
#         if self.pile[-1] == Card(Suit.WHOT, 20):
#             self.handle_whot(player)
#         if self.current_player._cards == []:
#             return
        
#         print(f"{player} Resume")

#     def handle_whot(self, player: Player):
#         """
#         Method to handle whot card
#         """

#         print(
#             f"{self.current_player} ask {player}  for any card suit of your choice"
#         )
#         print(f"{self.current_player}: {self.current_player._cards}")
#         suit = input("Suit of the card(STAR, CIRCLE, ANGLE, SQUARE, CROSS): ")
#         print(player._cards)
#         inp = int(input(f"{player} select a card with suit of {suit}: "))
#         returned_card = player._cards[inp]

#         if str(returned_card.suit) == suit:
#             player._cards.remove(returned_card)
#             self.pile.append(returned_card)

#             awarded_player = self.current_player
#             self.current_player = player
            
#             if returned_card.face == 1:
#                 self.handle_hold_on(awarded_player)
#             if returned_card.face == 14:
#                 self.handle_go_gen(player)
#             if returned_card.face == 8:
#                 self.handle_suspension(awarded_player)
#                 return
#             if returned_card.face == 2:
#                 self.handle_pick_two(awarded_player)
#             if returned_card == Card(Suit.WHOT, 20):
#                 self.handle_whot(awarded_player)


#             # self.next_player()
#         else:
#             print(f"{player} doesn't have the card. You go gen")
#             player.recieve(self.gen.deal_card(1))
#             print(f"{player} you recieved: {player._cards[-1]}")
#             print(f"{self.current_player} play any card of your choice: ")
#             print(f"{self.current_player._cards}")
#             inp = int(input("Please input card index: "))
#             self.pile.append(self.current_player._cards[inp])
#             self.current_player._cards.remove(self.current_player._cards[inp])
#             self.process()

#     def check_winner(self):
#         """
#         This function will be used to check the winner of the game 
#         based on who doesn't hac
#         """
#         for player in self.players:
#             if len(player._cards) == 0:
#                 return True
#         return False

#     def next_player(self, skip=1):
#         n = self.players.index(self.current_player)
#         try:
#             self.current_player = self.players[n + skip]
#         except IndexError:
#             self.current_player = self.players[0]

#     def get_next_player(self):
#         n = self.players.index(self.current_player)
#         try:
#             return self.players[n + 1]
#         except IndexError:
#             return self.players[0]
