# Game State for Six Card Golf

from dataclasses import dataclass
from typing import Optional

from classes import Card, Pile, Deck, Hand, deal
from scoring import score_hand
from view_models import GameView, HandView, CardView


class GameState:
    def __init__(self, player_names: list[str], target_score: int = 100, max_rounds: int | None = None):
        self.player_names = player_names
        self.num_players = len(player_names)

        self.messages: list[str] = []

        # game level tracking
        self.round_number = 0
        self.cumulative_scores = {name: 0 for name in self.player_names}
        self.last_round_scores = None             # dict[str,int] | None

        # game end thresholds
        self.target_score = target_score  # we will end the game when any player has >= target_score
        self.max_rounds = max_rounds  # optional: end game after N rounds (None => unlimited)

        # placeholders
        self.deck = None
        self.discard = None
        self.hands = []
        self.phase = "setup"

        # start the first round immediately upon inititalization
        self.start_new_round()

    def start_new_round(self) -> None:
        self.last_round_scores = None # really? it's already initialized to None in __init__()
        
        # initialize round objects
        self.deck = Deck()
        self.deck.shuffle()

        self.discard = Pile()

        self.hands = [Hand(player_id=i, player_name=name, max_cards=6) for i, name in enumerate(self.player_names)]
        deal(self.deck, self.hands, cards_each=6)
        
        # phase + setup state
        self.phase = "setup"
        self.setup_player_index = 0
        self.setup_flips_done = 0
        
        # play state
        self.turn_index = 0
        self.pending_drawn_card = None  # type: Card | None
        self.pending_draw_source = None  # "deck" or "discard" or None

        # end-of-round trigger state
        self.round_ending_player_index = None     # int | None
        self.final_turns_remaining = None         # int | None

        # prepare the discard pile
        top = self.deck.draw()
        top.reveal()
        self.discard.add(top)

        self.log(f"\n=== Starting Round {self.round_number + 1} ===")

    def log(self, msg: str) -> None:
        self.messages.append(msg)
        # limit log length
        if len(self.messages) > 6:
            self.messages = self.messages[-6:]

    @property
    def cycle_number(self) -> int:
        return self.turn_index // self.num_players

    @property
    def current_player_index(self) -> int:
        return self.turn_index % self.num_players

    @property
    def current_hand(self):
        return self.hands[self.current_player_index]
    
    @property
    def current_player_name(self):
        return self.current_hand.player_name

    @property
    def setup_hand(self) -> Hand:
        return self.hands[self.setup_player_index]
    
    
    def prompt(self) -> str:
        if self.phase == "setup":
            remaining = 2 - self.setup_flips_done
            return f"{self.setup_hand.player_name} (setup, {remaining} flip(s) left) > "
        elif self.phase =="play":
            if getattr(self, "pending_drawn_card", None) is None:
                return f"{self.current_player_name} (draw: deck | discard) > "
            else:
                return f"{self.current_player_name} (resolve: swap <0-5> | discard) > "
        else:    
            return "> "


    def submit_command(self, raw: str) -> dict:
        """
        Single point of entry for applying a use command to the game state, 
        either via Terminal or a GUI layer. Any UI layer should call this instead of specific handlers directly.
        """

        cmd = (raw or "").lower().strip()
        self.messages.clear()
        if not cmd:
            return {"state_changed": False, "phase": self.phase}
        
        before_phase = self.phase
        before_turn = getattr(self, "turn_index", None)

        if self.phase == "setup":
            self.interactive_hand_setup(cmd)
        
        if self.phase == "play":
            self.interactive_play_step(cmd)
        
        # other phases handled by gamerunner.py (round_over, game_over, unknown); no op by gamestate.py
        state_changed = (
            self.phase != before_phase 
            or getattr(self, "turn_index", None) != before_turn 
            or bool(self.messages)
        )

        return {"state_changed": state_changed, "phase": self.phase}
    
    def view(self) -> GameView:
        """
        Return a structured, UI-friendly snapshot of the current game state.
        No internal game objects are returned, only JSON-serializable data.
        """
        def card_view(c: Card) -> CardView:
            def filename_for_card(value: str, suit: str) -> str:
                value_map = {
                    "Ace":"ace", 
                    "King":"king", 
                    "Queen":"queen", 
                    "Jack":"jack", 
                    "10":"10", 
                    "9": "9", 
                    "8": "8", 
                    "7": "7", 
                    "6": "6", 
                    "5": "5", 
                    "4": "4", 
                    "3": "3", 
                    "2": "2" 
                }

                suit_map = {
                    "Spades": "spades",
                    "Hearts": "hearts",
                    "Clubs": "clubs",
                    "Diamonds": "diamonds"
                }

                return f"{value_map[value]}_of_{suit_map[suit]}.png"

            return CardView(
                face_up = c.faceUp,
                short = repr(c),
                long = c.display(),
                value = c.value,
                suit = c.suit,
                image = filename_for_card(c.value, c.suit) if c.faceUp else "back.png"
            )

        def hand_view(h: Hand) -> HandView:
            visible = score_hand(h, cancel_matching_columns=True, include_face_down=False)
            return HandView(
                player_id = h.player_id,
                player_name = h.player_name,
                visible_score = visible,
                cards = [card_view(c) for c in h.cards]
            )
        
        discard_top = card_view(self.discard.peek()) if self.discard.count() else None
        pending = card_view(self.pending_drawn_card) if self.pending_drawn_card else None

        active = None
        if self.phase == "setup":
            active = self.setup_player_index
        elif self.phase == "play":
            active = self.current_player_index

        return GameView(
            phase = self.phase,
            round_number = self.round_number,
            cycle_number = self.cycle_number,
            turn_index = self.turn_index,
            active_player_index = active,
            
            deck_count = self.deck.count(),
            discard_top = discard_top,
            pending_drawn = pending,
            hands = [hand_view(h) for h in self.hands],
            messages = list(self.messages),
            cumulative_scores = dict(self.cumulative_scores),
            last_round_scores = dict(self.last_round_scores) if self.last_round_scores else None,
            valid_actions = {}
        )
    

    def interactive_hand_setup(self, raw: str) -> None:
        """
        Interactively handle setup commands. Players must choose 2 cards in their hands to reveal.
        Accepts commands like 'flip 3' or just '3' where the number is the hand position of the card to flip.
        """
        cmd = raw.lower().strip()
        if not cmd:
            return
        
        # parse the command to extract the position of the card to flip
        pos = None
        parts = cmd.split()
        if len(parts) == 2 and parts[0] in ("flip", "reveal", "show") and parts[1].isdigit():
            pos = int(parts[1])
        elif len(parts) == 1 and parts[0].isdigit():
            pos = int(parts[0])

        if pos is None:
            self.log("Setup: Please select a card to flip. Type flip N, where N is a digit from 0 to 5 representing the position of the card to flip. (Or just enter the digit)")
            return
        if pos not in range(6): # needs to be 0..5
            self.log("Setup: Not a valid card position. Please choose a number from 0 to 5.")
            return

        hand = self.setup_hand

        if pos >= len(hand.cards):
            self.log("You don't have that many cards. Please choose another.")
            return

        # prevent picking a card that's already flipped
        if hand.cards[pos].faceUp:
            self.log("That card has already been revealed. Please choose another card.")
            return
        hand.cards[pos].reveal()
        self.log(f"{hand.player_name} flipped {pos}: {hand.cards[pos].display()}")
        self.setup_flips_done +=1


        if self.setup_flips_done >= 2:
            # move to next player
            self.setup_flips_done = 0
            self.setup_player_index += 1

            if self.setup_player_index >= self.num_players:
                self.phase = "play"
                self.turn_index = 0
                self.log("Setup complete. Begin play.")
            else:
                self.log(f"Setup: Now {self.setup_hand.player_name} flips 2 cards.")


    def interactive_play_step(self, raw: str) -> None:
        """
        Handle play commands.

        States:
            - If there is no pending drawn card, accept 'draw deck' or 'draw discard'
            - If a pending drawn card exists, accept 'swap N' or 'discard'
        """

        cmd = raw.lower().strip()
        if not cmd:
            return
        
        hand = self.current_hand

        # Draw a card
        if self.pending_drawn_card is None:
            if cmd in ("draw deck", "d deck", "deck", "e"):
                c = self.deck.draw()
                c.reveal()
                self.pending_drawn_card = c
                self.pending_draw_source = "deck"
                self.log(f"{hand.player_name} drew: {c.display()} (from deck)")
                return
            
            if cmd in ("draw discard", "d discard", "disc", "i"):
                if self.discard.count() == 0:
                    self.log("Discard pile is empty.")
                    return
                c = self.discard.draw()
                c.reveal()
                self.pending_drawn_card = c
                self.pending_draw_source = "discard"
                self.log(f"{hand.player_name} took: {c.display()} (from discard)")
                return
            
            self.log("Play: draw deck | draw discard")
            return
        
        # Resolve placement of drawn card (swap/discard)
        pending = self.pending_drawn_card

        if cmd in ("discard", "x", "dump"):
            pending.reveal()
            self.discard.add(pending)
            self.log(f"{hand.player_name} discarded: {pending.display()}")
            self._end_turn()
            return
        
        parts = cmd.lower().split()
        if len(parts) == 2 and parts[0] in ("swap", "s") and parts[1].isdigit():
            pos = int(parts[1])
            if pos not in range(6):
                self.log("Swap: choose a position 0-5.")
                return
            if pos >= len(hand.cards):
                self.log("Swap: you don't have that many cards.")
                return
            
            outgoing = hand.cards[pos]
            hand.cards[pos] = pending
            pending.reveal()

            outgoing.reveal()
            self.discard.add(outgoing)

            self.log(f"{hand.player_name} swapped into {pos}: {pending.display()}")
            self.log(f"Discarded from hand: {outgoing.display()}")

            self._end_turn()
            return
        
        self.log("Resolve: swap <0-5> | discard")

    def is_hand_complete(self, hand: Hand) -> bool:
        # assumes 6-card hands; safe if you ever change size
        return len(hand.cards) >= 6 and all(c.faceUp for c in hand.cards[:6])

    def reveal_all_hands(self) -> None:
        for h in self.hands:
            for c in h.cards:
                c.reveal()

    def _end_turn(self) -> None:
        self.pending_drawn_card = None
        self.pending_draw_source = None    
        just_finished = self.current_player_index  # player who just took the turn

        # print(f"[DEBUG] _end_turn called. Before increment: turn_index={self.turn_index}, current_player_index={self.current_player_index}")

        if self.round_ending_player_index is None:
            if self.is_hand_complete(self.hands[just_finished]):
                self.round_ending_player_index = just_finished
                self.final_turns_remaining = self.num_players - 1
                self.log(f"{self.player_names[just_finished]} completed their hand. Final turns remaining: {self.final_turns_remaining}")
        else:
            if just_finished != self.round_ending_player_index:
                self.final_turns_remaining -= 1
                self.log(f"Final turns remaining: {self.final_turns_remaining}")

        self.turn_index += 1

        if self.round_ending_player_index is not None and self.final_turns_remaining <= 0:
            self.end_round()

    def end_round(self) -> None:
        self.reveal_all_hands()
        round_scores: dict[str, int]  = {}
        for h in self.hands:
            name = h.player_name
            round_scores[name] = score_hand(h)

        for name, s in round_scores.items():
            self.cumulative_scores[name] += s

        self.last_round_scores = round_scores


        self.log("\n=== Round Over! Scoring: ===")
        for name, s in round_scores.items():
            self.log(f"{name}: {s}     (total: {self.cumulative_scores[name]})")

        self.round_number += 1
        game_over = False
        if self.target_score is not None and any(total >= self.target_score for total in self.cumulative_scores.values()):
            game_over = True
        if self.max_rounds is not None and self.round_number >= self.max_rounds:
            game_over = True
        
        if game_over:
            min_score = min(self.cumulative_scores.values())
            winners = [name for name, t in self.cumulative_scores.items() if t == min_score]

            if len(winners) == 1:
                self.log(f"\n=== GAME OVER === Winner: {winners[0]} with {min_score} points (lowest score wins).")
            else:
                self.log(f"\n=== GAME OVER === Tie between: {', '.join(winners)} (score: {min_score})")

            self.phase = "game_over"
        else:
            self.phase = "round_over"
            self.log(f"Round {self.round_number} complete.")




    def help_text(self) -> str:
        if self.phase == "setup":
            return "Setup: flip <0-5> (or just 0-5)."
        if self.phase == "play":
            if self.pending_drawn_card is None:
                return "Play: draw deck | draw discard"
            return "Resolve: swap <0-5> | discard"
        return ""