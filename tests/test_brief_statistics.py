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


def test_brief_statistics_bold_headings():
    brief = "**Definitions**\n\nA.\n\n**Unverified**\n\nB.\n\n**Statistics**\n\n1. 44% ...\n\n**Unverified**\n\nC."
    assert brief_statistics(brief) == "\n\n## Research brief: statistics\n\n1. 44% ..."


def test_statistics_file_wins(tmp_path):
    import review_post
    review_post.ROOT = tmp_path
    out = tmp_path / "a-output"; out.mkdir()
    (out / "a-research.md").write_text("**Statistics**\n\nold\n\n**Unverified**\n")
    assert review_post._statistics_for("a").endswith("old")
    (out / "a-statistics.md").write_text("1. 44% ... | https://x.com\n")
    assert review_post._statistics_for("a") == "\n\n## Research brief: statistics\n\n1. 44% ... | https://x.com"
