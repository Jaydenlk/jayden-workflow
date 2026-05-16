import json
import os


STATE_DIR = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR", "."), ".claude", "state")
TRACKER_PATH = os.path.join(STATE_DIR, "decision-tracker.json")


def main():
    if os.path.exists(TRACKER_PATH):
        try:
            with open(TRACKER_PATH, "r", encoding="utf-8") as f:
                tracker = json.load(f)
            tracker["nudge_count"] = 0
            with open(TRACKER_PATH, "w", encoding="utf-8") as f:
                json.dump(tracker, f, indent=2)
        except (json.JSONDecodeError, OSError):
            pass


if __name__ == "__main__":
    main()
