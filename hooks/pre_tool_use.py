import json
import os


STATE_DIR = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR", "."), ".claude", "state")
TRACKER_PATH = os.path.join(STATE_DIR, "decision-tracker.json")


def main():
    if not os.path.exists(TRACKER_PATH):
        return
    try:
        with open(TRACKER_PATH, "r", encoding="utf-8") as f:
            tracker = json.load(f)
    except (json.JSONDecodeError, OSError):
        return
    pending = tracker.get("pending_decisions", [])
    if pending:
        nodes = ", ".join(pending)
        print(
            f"[HOOK] Unrecorded decision nodes detected: {nodes}. "
            f"Please invoke the decision-recorder agent before continuing with code changes."
        )


if __name__ == "__main__":
    main()
