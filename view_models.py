from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CardView:
    face_up: bool
    short: str
    long: str
    value: str
    suit: str
    image: str


@dataclass
class HandView:
    player_id: int
    player_name: str
    visible_score: int
    cards: List[CardView]


@dataclass
class GameView:
    phase: str
    round_number: int
    cycle_number: int
    turn_index: int
    active_player_index: Optional[int]
    deck_count: int
    discard_top: Optional[CardView]
    pending_drawn: Optional[CardView]
    hands: List[HandView]
    messages: List[str]
    cumulative_scores: dict[str, int]
    last_round_scores: Optional[dict[str, int]]
    valid_actions: dict
