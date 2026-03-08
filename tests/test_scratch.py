# test_scratch.py

from classes import Deck, Card, Pile, Hand, deal, create_hands
from gamestate import GameState

def main():
    print("\n=== Creating deck ===")
    deck = Deck()
    print("Deck size:", deck.count())

    print("\n=== Shuffling deck ===")
    deck.shuffle()
    print(deck)  # uses __repr__

    print("\n=== Dealing hands ===")
    hands = create_hands(player_names=["Alice", "Bob"], max_cards=6)
    deal(deck, hands, cards_each=6)

    print("\n=== Initial hands (all face down) ===")
    for h in hands:
        print(h)

    print("\n=== Reveal some cards for testing ===")
    hands[0].cards[0].reveal()
    hands[0].cards[3].reveal()
    hands[1].cards[0].reveal()
    hands[1].cards[3].reveal()

    for h in hands:
        print(h)

    print("\n=== Drawing from deck ===")
    card = deck.draw()
    card.reveal()
    print("Drew:", card)
    print("Deck now:", deck)

    return deck, hands, card


if __name__ == "__main__":
    main()