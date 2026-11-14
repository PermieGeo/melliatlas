"""Enable the project formatter in an existing local apatch configuration."""

import re
from pathlib import Path

FORMAT_COMMAND = 'format_commands:\n  - ["sh", "./run-format.sh"]'


def enable_formatter(config_path: Path) -> bool:
    if config_path.is_symlink() or not config_path.is_file():
        raise ValueError("Expected a regular existing .apatch/config.yaml; inspect it manually")

    content = config_path.read_text(encoding="utf-8")
    if not re.search(r"(?m)^schema_version:\s*1\s*$", content):
        raise ValueError("Expected schema_version: 1; inspect config.yaml manually")
    if not re.search(r"(?m)^checks:\s*(?:\S.*)?$", content):
        raise ValueError("No existing checks configuration; inspect config.yaml manually")

    existing = re.search(r"(?m)^format_commands:[^\n]*(?:\n[ \t]+[^\n]*)*", content)
    if existing:
        if existing.group().strip() == FORMAT_COMMAND:
            return False
        raise ValueError("Existing format_commands differ; review config.yaml manually")

    config_path.write_text(content.rstrip("\n") + "\n" + FORMAT_COMMAND + "\n", encoding="utf-8")
    return True


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    config = root / ".apatch" / "config.yaml"
    changed = enable_formatter(config)
    print("Configured apatch FMT" if changed else "apatch FMT already configured")


if __name__ == "__main__":
    main()
