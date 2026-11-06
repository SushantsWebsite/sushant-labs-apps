"""Pure logic for Typing Speed Test. No tkinter here so it can be unit-tested."""
import json
import random
import time
from pathlib import Path

SCORES_PATH = Path.home() / ".sushant_labs" / "typing_scores.json"

WORDS = (
    "the be to of and a in that have it for not on with he as you do at this but his by from they we say "
    "her she or an will my one all would there their what so up out if about who get which go me when make "
    "can like time no just him know take people into year your good some could them see other than then now "
    "look only come its over think also back after use two how our work first well way even new want because "
    "any these give day most us keep world still hand life tell turn place small light stay build ship"
).split()


def make_text(n_words: int = 60, rng=None) -> str:
    rng = rng or random
    return " ".join(rng.choice(WORDS) for _ in range(n_words))


def correct_chars(typed: str, target: str) -> int:
    return sum(1 for a, b in zip(typed, target) if a == b)


def accuracy(typed: str, target: str) -> float:
    if not typed:
        return 0.0
    return round(100 * correct_chars(typed, target) / len(typed), 1)


def wpm(correct: int, seconds: float) -> float:
    """Standard WPM: one word = 5 characters."""
    if seconds <= 0:
        return 0.0
    return round((correct / 5) / (seconds / 60), 1)


def load_scores(path=SCORES_PATH) -> list:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def save_score(path, speed: float, acc: float, keep: int = 50) -> list:
    path = Path(path)
    scores = load_scores(path)
    scores.append({"wpm": speed, "accuracy": acc, "ts": int(time.time())})
    scores = scores[-keep:]
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(scores), encoding="utf-8")
    except OSError:
        pass  # a read-only home folder must never crash the app
    return scores


def best_wpm(scores: list):
    values = [s.get("wpm", 0) for s in scores if isinstance(s, dict)]
    return max(values) if values else None
