"""Refreshes the offline copy: `python -m app.live` (from apps/api, with internet)."""

import asyncio
import json
import sys

from .service import SNAPSHOT_PATH, build_snapshot, read_snapshot


def main() -> int:
    data, errors = asyncio.run(build_snapshot(read_snapshot()))
    SNAPSHOT_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(f"Guardado {SNAPSHOT_PATH}")
    for key, part in data.items():
        state = f"SIN ACTUALIZAR ({errors[key]})" if key in errors else "actualizado"
        print(f"  {key}: {state}, data from {part['fetched_at']}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
