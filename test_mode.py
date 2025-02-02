from whot import *

w = Whot()

test_pile = Card(Suit.CIRCLE, 14)

card1 = Card(Suit.WHOT, 20)
card2 = Card(Suit.TRIANGLE, 14)
card3 = Card(Suit.SQUARE, 2)
card4 = Card(Suit.STAR, 8)
card5 = Card(Suit.CROSS, 1)

test_player =  [card1, card2, card3, card4, card5]

w = Whot()

w.test_mode(test_pile, test_player)

w.start_game()

print(w.game_state())