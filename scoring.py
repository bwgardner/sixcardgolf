from typing import Dict, List, Tuple, Optional

DEFAULT_CARD_SCORES: Dict[str, int] = {
    "Ace": 1,
    "King": 0,
    "Queen": 10,
    "Jack": 10,
    "10": 10,
    "9": 9,
    "8": 8,
    "7": 7,
    "6": 6,
    "5": 5,
    "4": 4,
    "3": 3,
    "2": -2
}

COLUMNS_2x3: List[Tuple[int, int]] = [(0,3), (1,4), (2,5)]

def score_hand(
        hand,
        card_scores: Dict[str, int] = DEFAULT_CARD_SCORES,
        cancel_matching_columns: bool = True,
        include_face_down: bool = False,
) -> int:
    """
    Score a Six Card Golf hand (2x3 layout).
    
    :param cancel_matching_columns: if True, matching ranks in a column cancel to 0.
    :param include_face_down: if False, facedown cards are ignored (scored as 0 for now). If True, facedown cards are scored by their value.
    """

    cards = hand.cards

    def card_value(i: int) -> Optional[str]:
        if i >= len(cards):
            return None
        c = cards[i]
        if (not c.faceUp) and (not include_face_down):
            return None
        return c.value
    
    total = 0

    for a, b in COLUMNS_2x3:
        va = card_value(a)
        vb = card_value(b)

        # If one of the cards is face down, treat as 0 contribution and move on
        if va is None and vb is None:
            continue

        # Check if column cancellation applies
        if cancel_matching_columns and (va is not None) and (vb is not None) and (va == vb):
            continue

        if va is not None:
            total += card_scores.get(va, 0)
        if vb is not None:
            total += card_scores.get(vb, 0)

    return total

def score_all_players(game_state, **kwargs) -> Dict[str, int]:
    """
    Returns a Dictionary of {player_name: score}
    """

    out: Dict[str, int] = {}
    for h in game_state.hands:
        name = getattr(h, "playerName", None) or getattr(h, "player_name", None) or "Player"
        out[name] = score_hand(h, **kwargs)
    return out
