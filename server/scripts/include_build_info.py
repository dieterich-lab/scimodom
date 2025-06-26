"""Script: include_build_info.py."""

import argparse
from datetime import datetime, timezone
from pathlib import Path

import scimodom
from alembic.config import Config
from alembic.script import ScriptDirectory

from scimodom import __version__ as package_version
from scimodom.services.url import API_VERSION

# server/ (dev) or /install/ (image build)
SERVER_DIR = Path(__file__).resolve().parent.parent


def main() -> None:
    """Include build info into the application."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--commit-date", required=True)
    args = parser.parse_args()

    cfg = Config(str(SERVER_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(SERVER_DIR / "migrations"))
    expected_revision = ScriptDirectory.from_config(cfg).get_current_head()

    info = {
        "build": {
            "tag": args.tag,
            "commit": args.commit,
            "commit_date": args.commit_date,
            "version": package_version,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "api": {"version": API_VERSION},
        "database": {"expected_revision": expected_revision},
    }

    out = Path(scimodom.__file__).parent / "_build_info.py"
    out.write_text(f"BUILD_INFO = {info!r}\n")
    out.write_text("# Auto-generated at build time\n" f"BUILD_INFO = {info!r}\n")


if __name__ == "__main__":
    main()
