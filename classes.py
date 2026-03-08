# classes for sixCardGolf game

import random
from dataclasses import dataclass

# default card deck
VALUE_LIST = [
    "Ace",
    "King",
    "Queen",
    "Jack",
    "10",
    "9",
    "8",
    "7",
    "6",
    "5",
    "4",
    "3",
    "2"
]

SUIT_LIST = [
    "Spades",
    "Clubs",
    "Diamonds",
    "Hearts"
]

@dataclass
class Card:
    value: str
    suit: str
    faceUp: bool = False

    def display(self) -> str:
        return f"{self.value} of {self.suit}" if self.faceUp else "A face down card"

    def reveal(self):
        self.faceUp = True

    def hide(self):
        self.faceUp = False    

    def flip(self):
        self.faceUp =  not self.faceUp

    def shortname(self) -> str:
        if not self.faceUp:
            return "XX"
        
        value_map = {"Ace":"A", "King":"K", "Queen":"Q", "Jack":"J", "10":"10"}
        v = value_map.get(self.value, self.value)
        s = self.suit[0]
        return f"{v}{s}"
    
    def __repr__(self):
        return self.shortname()
    
    def __str__(self):
        return self.display()
    

class Pile:
    """A generic stack of Cards, to be used for Hand, Deck, Discard Pile, etc."""
    def __init__(self, cards=None):
        self.cards = list(cards) if cards else []

    def count(self) -> int:
        return len(self.cards)
    
    def peek(self):
        """Peek at the topmost card without drawing it"""
        return self.cards[-1] if self.cards else None
    
    def draw(self) -> Card:
        if not self.cards:
            raise RuntimeError("Cannot draw a card: pile is empty.")
        return self.cards.pop()
    
    def add(self, cards, addToTop=True):
        """Adds cards to the pile (default on top); cards can be a single Card or an iterable of Cards."""
        if isinstance(cards, Card):
            cards = [cards]
        if addToTop:
            self.cards.extend(cards)
        else:
            self.cards = list(cards) + self.cards

    def display(self):
        for c in self.cards:
            print(c.display())

    def reveal_all(self):
        for c in self.cards:
            c.reveal()

    def hide_all(self):
        for c in self.cards:
            c.hide()

    def flip_all(self):
        for c in self.cards:
            c.flip()

    def apply(self, fn):
        for c in self.cards:
            fn(c)

    def __repr__(self):
        # generic repr for any pile (deck/discard/etc.)
        return "[" + ", ".join(repr(c) for c in self.cards) + "]"
    
    def __str__(self):
        return repr(self)


class Deck(Pile):
    def __init__(self, valueList=VALUE_LIST, suitList=SUIT_LIST):
        super().__init__([Card(v, s, False) for v in valueList for s in suitList])

    def shuffle(self):
        random.shuffle(self.cards)
        print("The deck has been shuffled")

    def reset(self, valueList=VALUE_LIST, suitList=SUIT_LIST):
        self.cards = [Card(v, s, False) for v in valueList for s in suitList]
        self.shuffle()

class Hand(Pile):
    def __init__(self, player_id: int, player_name: str = "", max_cards: int | None = None):
        super().__init__(cards=[])
        self.player_id = player_id
        self.player_name = player_name or f"Player {player_id}"
        self.max_cards = max_cards

    def add(self, cards, addToTop=True):
        # enforce max_cards if provided
        incoming = [cards] if isinstance(cards, Card) else list(cards)
        if self.max_cards is not None and self.count() + len(incoming) > self.max_cards:
            raise RuntimeError(f"{self.player_name}'s hand would exceed max_cards={self.max_cards}.")
        super().add(incoming, addToTop=addToTop)

    def show(self, show_face_down_as="XX"):
        parts=[]
        for c in self.cards:
            parts.append(c.shortname() if c.faceUp else show_face_down_as)
        print(f"{self.player_name}: " + " ".join(parts))

    def _render_grid(self, indexed: bool) -> list[str]:
        def cell(i: int) -> str:
            if i >= len(self.cards):
                return f"{i}:  " if indexed else "  " # empty slot if fewer than 6 cards
            if indexed:
                return f"{i}:{repr(self.cards[i])}" # uses Card.__repr__()
            return repr(self.cards[i])

        row1 = [cell(0), cell(1), cell(2)]
        row2 = [cell(3), cell(4), cell(5)]

        return [
            f"[{row1[0]:>7} {row1[1]:>7} {row1[2]:>7}]",
            f"[{row2[0]:>7} {row2[1]:>7} {row2[2]:>7}]"
        ]
    
    def grid_view(self) -> str:
        return f"{self.player_name}\n" + "\n".join(self._render_grid(indexed=False))

    def indexed_grid_view(self) -> str:
        return f"{self.player_name}\n" + "\n".join(self._render_grid(indexed=True))

    def __repr__(self):
        return self.indexed_grid_view()
    
    def __str__(self):
        return self.grid_view()
        


# Helper functions

def create_hands(player_names: list[str], max_cards: int | None = None) -> list[Hand]:
    return [Hand(player_id=i, player_name=name, max_cards=max_cards) for i, name in enumerate(player_names)]

def deal(deck: Deck, hands: list[Hand], cards_each: int) -> None:
    for _ in range(cards_each):
        for h in hands:
            h.add(deck.draw())
    
