#webapp.py
from __future__ import annotations
from dataclasses import asdict
from flask import Flask, jsonify, request, render_template
from gamestate import GameState
import os


app = Flask(__name__)


def make_game() -> GameState:
    # helper function to instantiate a clean new game
    target_score = int(os.getenv("SIXGOLF_TARGET_SCORE", "100"))
    mr = os.getenv("SIXGOLF_MAX_ROUNDS", "").strip()
    max_rounds = int(mr) if mr else None
    return GameState(["Alice", "Bob"], target_score=target_score, max_rounds=max_rounds)


def state_dict() -> dict:
    # convert GameView dataclass -> JSON serializable plain dict
    return asdict(game.view())


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/state")
def get_state():
    return jsonify(state_dict())


@app.post("/command")
def post_command():
    data = request.get_json(silent=True) or {}
    cmd = str(data.get("cmd", "")).lower().strip()

    if cmd in ("q", "quit", "exit"):
        return jsonify({"ok": True, "quit": True, "state": state_dict()})
    
    if cmd:
        game.submit_command(cmd)

    return jsonify({"ok": True, "state": state_dict()})


@app.post("/new_round")
def new_round():
    game.start_new_round()
    return jsonify({"ok": True, "state": state_dict()})


@app.post("/reset")
def reset_game():
    global game
    game = make_game()
    return jsonify({"ok": True, "state": state_dict()})

#instantiate game
game = make_game()

if __name__ == "__main__":
    # http://127.0.0.1:5000
    app.run(debug=True)