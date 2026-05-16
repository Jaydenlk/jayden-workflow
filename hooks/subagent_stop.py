import json
import sys


def main():
    data = json.load(sys.stdin)
    agent_type = data.get("agent_type", "")
    audit_targets = {"implementer", "test-agent"}
    if agent_type in audit_targets:
        print(
            f"[HOOK] Subagent '{agent_type}' completed. "
            f"Per team protocol, this output MUST be audited by the reviewer agent before integration. "
            f"Please invoke the reviewer agent now."
        )


if __name__ == "__main__":
    main()
