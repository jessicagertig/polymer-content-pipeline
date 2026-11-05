"""brief_statistics self-check."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from review_post import brief_statistics  # noqa: E402


def test_brief_statistics():
    brief = "## Definitions\n\nA.\n\n## Unverified\n\nB.\n\n## Statistics\n\n1. 94% ...\nSource: X | https://x.com/a\n\n## Unverified\n\nC."
    assert brief_statistics(brief) == "\n\n## Research brief: statistics\n\n1. 94% ...\nSource: X | https://x.com/a"
    assert brief_statistics("## Definitions\n\nA.") == ""
    assert brief_statistics("## Statistics\n\n1. 5%").endswith("1. 5%")
