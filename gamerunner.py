# gamerunner.py

from gamestate import GameState
from scoring import score_hand
from view_models import GameView, HandView, CardView
import os
    
KNOWN_PHASES = {"setup", "play", "round_over", "game_over"}


def render(game: GameState) -> None:
    """Render current game state in terminal"""
    v: GameView = game.view()
    
    print("\n" * 2)
    
    active = v.active_player_index
    
    for i, h in enumerate(v.hands):
        header = f">> {h.player_name} <<" if i == (active is not None and i == active) else h.player_name
        print(f"{header}  (visible score: {h.visible_score})")
        
        def cell(idx: int) -> str:
            if idx >= len(h.cards):
                return f"{idx}:  "
            return f"{idx}:{h.cards[idx].short}"
        
        row1 = [cell(0), cell(1), cell(2)]
        row2 = [cell(3), cell(4), cell(5)]

        print(f"[{row1[0]:>7} {row1[1]:>7} {row1[2]:>7}]")
        print(f"[{row2[0]:>7} {row2[1]:>7} {row2[2]:>7}]")
        print()

    discard_short = v.discard_top.short if v.discard_top is not None else "(empty)"
    drawn_long = v.pending_drawn.long if v.pending_drawn is not None else "(none)"

    print("-" * 40)
    print(
        f"Phase: {v.phase} | "
        f"Round: {v.round_number} | "
        f"Deck: {v.deck_count} cards | " 
        f"Discard top: {discard_short} | " 
        f"Drawn: {drawn_long}"
        )
    
    if v.messages:
        print()
        for m in v.messages[-4:]:
            print(m)
    print()

    return True

def main():
    player_names = ["Alice", "Bob"]
    target_score = int(os.getenv("SIXGOLF_TARGET_SCORE", "100"))
    mr = os.getenv("SIXGOLF_MAX_ROUNDS", "").strip()
    max_rounds = int(mr) if mr else None
    game = GameState(player_names, target_score=target_score, max_rounds=max_rounds)


    print("Six Card Golf (WIP)")
    print("Global commands: help, quit\n")

    while True:
        render(game)
        v = game.view()
        
        # phase-related commands
        if v.phase == "round_over":
            ans = input("Play another round? (y/n)> ").strip().lower()
            if ans.startswith("y"):
                game.start_new_round()
                continue
            break

        if v.phase == "game_over":
            input("Game finished. Press <Enter> key to exit.")
            break

        if v.phase not in ("setup", "play"):
            print(f"[ERROR] Unknown phase '{v.phase}'. Exiting.")
            break

        # gameplay commands
        cmd = input(game.prompt()).lower().strip()

        if cmd in ("q", "quit", "exit"):
            break

        if cmd in ("h", "help", "?"):
            print(game.help_text())
            continue

        game.submit_command(cmd)

    print("Goodbye!")

    
if __name__ == "__main__":
    main()