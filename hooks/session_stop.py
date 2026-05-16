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
            f"[HOOK] Session ending with {len(pending)} unrecorded decision(s): {nodes}. "
            f"These decisions will be lost after /clear. "
            f"Consider invoking the decision-recorder agent before ending."
        )


if __name__ == "__main__":
    main()
