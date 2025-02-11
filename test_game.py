import unittest
from whot import *

class TestWhot(unittest.TestCase):
    
    def test_pick_two(self):
        pile = Card(Suit.CIRCLE, 3)

        card1 = Card(Suit.CIRCLE, 2)
        card2 = Card(Suit.WHOT, 20)

        test_player = [card1, card2]

        w = Whot(4, 2)

        w.test_mode(pile, test_player)

        w.start_game()

        w.play(0)

        self.assertEqual(len(w.game_state()["player_1"]), 1)
        self.assertEqual(len(w.game_state()["player_2"]), 4)
        self.assertEqual(len(w.game_state()["player_3"]), 2)
        self.assertEqual(len(w.game_state()["player_3"]), 2)

    def test_go_gen(self):
        pile = Card(Suit.CIRCLE, 3)

        card1 = Card(Suit.CIRCLE, 14)
        card2 = Card(Suit.WHOT, 20)

        test_player = [card1, card2]

        w = Whot(4, 2)

        w.test_mode(pile, test_player)

        w.start_game()

        w.play(0)

        self.assertEqual(len(w.game_state()["player_1"]), 1)
        self.assertEqual(len(w.game_state()["player_2"]), 3)
        self.assertEqual(len(w.game_state()["player_3"]), 3)
        self.assertEqual(len(w.game_state()["player_3"]), 3)

    def test_suspension(self):
        pile = Card(Suit.CIRCLE, 3)

        card1 = Card(Suit.CIRCLE, 8)
        card2 = Card(Suit.WHOT, 20)

        test_player = [card1, card2]

        w = Whot(3, 2)

        w.test_mode(pile, test_player)

        w.start_game()

        w.play(0)

        self.assertEqual(w.game_state()["current_player"], "player_3")    

    def test_hold_on(self):
        pile = Card(Suit.CIRCLE, 3)

        card1 = Card(Suit.CIRCLE, 1)
        card2 = Card(Suit.CIRCLE, 4)
        card3 = Card(Suit.WHOT, 20)

        test_player = [card1, card2, card3]

        w = Whot(3, 3)

        w.test_mode(pile, test_player)

        w.start_game()

        w.play(0)

        self.assertEqual(w.game_state()["current_player"], "player_1")    

        w.play(0)

        self.assertEqual(len(w.game_state()["player_1"]), 1)
        self.assertEqual(w.game_state()["current_player"], "player_2")


    def test_whot(self):
        pile = Card(Suit.SQUARE, 3)

        card1 = Card(Suit.CIRCLE, 1)
        card2 = Card(Suit.CIRCLE, 4)
        card3 = Card(Suit.WHOT, 20)

        test_player = [card1, card2, card3]

        w = Whot(3, 3)

        w.test_mode(pile, test_player)

        w.start_game()

        w.play(2)
        self.assertEqual(w.game_state()["current_player"], "player_1")    

        w.request("circle")
        
        self.assertEqual(w.request_mode, True)


if __name__ == '__main__':
    unittest.main()