# test_autoplay.py
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAMERUNNER = ROOT / "gamerunner.py"

def build_round_script() -> list[str]:
    """
    Commands to complete one round with 2 players.

    Setup:
      Alice flips 0 and 3
      Bob flips 1 and 4

    Play strategy:
      Always 'draw deck' then 'swap N' where N is a face-down slot for that player.
      This guarantees each player eventually has all 6 face up -> round end triggers.
    """
    cmds: list[str] = []

    # setup
    cmds += ["0", "3", "1", "4"]

    # play (8 turns: Alice/Bob alternating; each swap reveals a new slot)
    turns = [
        ("Alice", 1),
        ("Bob", 0),
        ("Alice", 2),
        ("Bob", 2),
        ("Alice", 4),
        ("Bob", 3),
        ("Alice", 5),  # Alice should now be complete => triggers end countdown
        ("Bob", 5),    # Bob gets final turn => round should end after this
    ]

    for _name, pos in turns:
        cmds.append("draw deck")
        cmds.append(f"swap {pos}")

    return cmds


def run_autoplay(stdin: str, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)

    return subprocess.run(
        [sys.executable, "-u", str(GAMERUNNER)],
        input=stdin,
        text=True,
        cwd=str(ROOT),
        capture_output=True,
        env=env
    )


def test_two_rounds_then_quit() -> None:
    script: list[str] = []

    # Round 1
    script += build_round_script()
    script += ["y"]  # play another round?

    # Round 2
    script += build_round_script()
    script += ["n"]  # stop after round 2

    stdin = "\n".join(script) + "\n"
    result = run_autoplay(stdin)

    out = result.stdout or ""
    err = result.stderr or ""

    # Debug on failure
    assert result.returncode == 0, f"Return code {result.returncode}\nSTDERR:\n{err}\nSTDOUT:\n{out}"

    # Round starts (from GameState.start_new_round log)
    assert "=== Starting Round 1 ===" in out, "Missing 'Starting Round 1' banner"
    assert "=== Starting Round 2 ===" in out, "Missing 'Starting Round 2' banner"

    # Round scoring banner (from GameState.end_round log)
    assert out.count("=== Round Over! Scoring: ===") >= 2, "Expected scoring banner at least twice"

    # Totals should be printed
    assert "(total:" in out, "Expected cumulative totals '(total: ...)' in output"

    # Clean exit
    assert "Goodbye!" in out, "Expected 'Goodbye!' in output"

    # No crashes
    assert "Traceback" not in out
    assert "Traceback" not in err


def test_game_over_by_max_rounds() -> None:
    script = []
    script += build_round_script()
    script += ["y"]
    script += build_round_script()
    # after game_over your runner may prompt "Press Enter"; provide one blank line
    script += [""]

    stdin = "\n".join(script) + "\n"
    result = run_autoplay(stdin, extra_env={"SIXGOLF_MAX_ROUNDS": "2", "SIXGOLF_TARGET_SCORE": "100"})

    out = result.stdout or ""
    err = result.stderr or ""

    assert result.returncode == 0, f"Return code {result.returncode}\nSTDERR:\n{err}\nSTDOUT:\n{out}"
    assert "=== Starting Round 1 ===" in out
    assert "=== Starting Round 2 ===" in out
    assert out.count("=== Round Over! Scoring: ===") >= 2
    assert "=== GAME OVER ===" in out


# def main():
#     test_two_rounds_then_quit()
#     print("✅ test_two_rounds_then_quit passed")

#     # Requires the gamerunner env-var hook.
#     test_game_over_by_max_rounds()
#     print("✅ test_game_over_by_max_rounds passed")


# if __name__ == "__main__":
#     main()