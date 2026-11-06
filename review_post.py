"""Check a staged post by the rules, section by section, then check its transitions across the whole post.

Usage:
  python review_post.py --check <slug> [<slug> ...]          the check loop on every section
  python review_post.py --check-opening <slug> [<slug> ...]  the check loop on the opening only
  python review_post.py --content <slug> [<slug> ...]        the whole-article content check
  python review_post.py --transitions <slug> [<slug> ...]    the whole-post transition pass

Each reads <slug>-output/<slug>.json and writes the result back to it, with a record in
<slug>-output/. Nothing goes to Sanity unless STAGE_TO_SANITY=true.
"""

import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from config.settings import settings
from connectors import sanity
from lib.llm import structured_call, cost, usage_line
from lib.logging import get
from lib import resources as res
from lib.repo import ROOT
from prompts.research import EDITOR_BRIEF
from lib.text import word_count, reading_time, space_em_dashes
from main import _save_output
from models.content import ContentPage
from prompts.review import (
    REVIEW_SYSTEM, FIX_USER, FIX_SCHEMA, FIND_RULE_BY_RULE_USER, FIND_RULE_BY_RULE_SCHEMA,
    TRANSITIONS_FIND_USER, TRANSITIONS_FIND_SCHEMA, TRANSITIONS_FIX_USER, POST_FIX_SCHEMA,
    REVIEW_CHANGES_USER, REVIEW_FIX_USER, OPENING_FIND_USER, OPENING_FIX_USER,
    CONTENT_RULES, CONTENT_FIXES, CONTENT_FIND_USER, CONTENT_FIND_SCHEMA, CONTENT_FIX_USER, CONTENT_FIX_SCHEMA,
    CONTENT_REVIEW_CHANGES_USER, CONTENT_REVIEW_FIX_USER,
    RESOURCE_SYSTEM, RESOURCE_CHECK_USER, RESOURCE_CHECK_SCHEMA, RESOURCE_FIX_USER, RESOURCE_FIX_SCHEMA,
    COMPETITOR_LINKS_SYSTEM, COMPETITOR_LINKS_USER, COMPETITOR_LINKS_SCHEMA,
    OPENING_FIX_SYSTEM, FIX_SYSTEM, TRANSITIONS_FIX_SYSTEM, REVIEW_FIX_SYSTEM, CONTENT_FIX_SYSTEM, CONTENT_REVIEW_FIX_SYSTEM,
)

log = get(__name__)


def reader_rule() -> str:
    """The reader paragraph of the writing guide, from the guide file."""
    guide = settings.brand_guidelines()
    start = guide.index("The reader doesn't have your context")
    end = guide.index("\n", start)
    return guide[start:end].strip()


def voice_section() -> str:
    """The Voice section of the writing guide, from the guide file."""
    guide = settings.brand_guidelines()
    start = guide.index("## Voice")
    end = guide.index("\n---", start)
    return guide[start:end].strip()


def tone_section() -> str:
    """The Tone section of the writing guide, from the guide file."""
    guide = settings.brand_guidelines()
    start = guide.index("## Tone")
    end = guide.index("\n---", start)
    return guide[start:end].strip()


def transition_rule() -> str:
    """The transition rule, from the Structure block of the writer's system prompt."""
    from prompts.content import CONTENT_SYSTEM
    start = CONTENT_SYSTEM.index("You are writing an article.")
    end = CONTENT_SYSTEM.index("a series of H3 sections is not a list.", start) + len("a series of H3 sections is not a list.")
    return CONTENT_SYSTEM[start:end].strip()


def section_rule() -> str:
    """The section rule, from the Structure block of the writer's system prompt."""
    from prompts.content import CONTENT_SYSTEM
    start = CONTENT_SYSTEM.index("Each section gives the reader what its heading promises")
    end = CONTENT_SYSTEM.index("draw a conclusion from the section.", start) + len("draw a conclusion from the section.")
    return CONTENT_SYSTEM[start:end].strip()


def numbers_rules() -> str:
    """The Numbers and statistics block, from the writer's system prompt."""
    from prompts.content import CONTENT_SYSTEM
    start = CONTENT_SYSTEM.index("**Numbers and statistics:**") + len("**Numbers and statistics:**")
    end = CONTENT_SYSTEM.index("**Logic:**", start)
    return CONTENT_SYSTEM[start:end].strip()


def opening_rules() -> str:
    """The Opening block and its examples, from the writer's system prompt."""
    from prompts.content import CONTENT_SYSTEM
    start = CONTENT_SYSTEM.index("**Opening:**")
    return CONTENT_SYSTEM[start:CONTENT_SYSTEM.index("**Structure:**", start)].strip()


def items_in_a_set_rule() -> str:
    """The items-in-a-set rule, from the Structure block of the writer's system prompt."""
    from prompts.content import CONTENT_SYSTEM
    start = CONTENT_SYSTEM.index("When the article gives a template, an example, or a rubric for each item in a set")
    end = CONTENT_SYSTEM.index("such as a behavioral interview matrix.", start) + len("such as a behavioral interview matrix.")
    return CONTENT_SYSTEM[start:end].strip()


def numbering_rule() -> str:
    """The numbering rule, from the Structure block of the writer's system prompt."""
    from prompts.content import CONTENT_SYSTEM
    start = CONTENT_SYSTEM.index("Number H3 sections only when")
    end = CONTENT_SYSTEM.index("the numbers imply the set is complete.", start) + len("the numbers imply the set is complete.")
    return CONTENT_SYSTEM[start:end].strip()


def opening_logic_rules() -> str:
    """The four logic checks, from the opening writer's request (OPENING_USER in rewrite_opening.py)."""
    from rewrite_opening import OPENING_USER
    start = OPENING_USER.index("First, wherever the draft gives a reason")
    end = OPENING_USER.index("so ranges are acceptable.", start) + len("so ranges are acceptable.")
    return OPENING_USER[start:end].strip()


def split_sections(body_html: str) -> list[str]:
    """The opening, then one string per <h2> section (its H3s included)."""
    starts = [m.start() for m in re.finditer(r"<h2[\s>]", body_html, flags=re.I)]
    if not starts:
        return [body_html]
    bounds = [0] + starts + [len(body_html)]
    parts = [body_html[bounds[i]:bounds[i + 1]] for i in range(len(bounds) - 1)]
    return [p for p in parts if p.strip()]


def _strip(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).strip()


def _section_name(section: str) -> str:
    heading = re.search(r"<h2[^>]*>(.*?)</h2>", section, flags=re.I | re.S)
    return re.sub("<[^>]+>", "", heading.group(1)) if heading else "Opening"


def _is_opening(section: str) -> bool:
    return not re.search(r"<h2[\s>]", section, flags=re.I)


def _opening_count_faults(section: str) -> list[str]:
    """The opening's word and paragraph limits, counted here because the model cannot count."""
    paragraphs = re.findall(r"<p[\s>].*?</p>", section, flags=re.I | re.S)
    faults = []
    words = word_count(section)
    if not 100 <= words <= 220:
        faults.append(f"The whole opening ||| Opening length ||| The opening is {words} words. The limit is 100 to 220 words.")
    if not 3 <= len(paragraphs) <= 4:
        faults.append(f"The whole opening ||| Opening paragraphs ||| The opening has {len(paragraphs)} paragraphs. It must have three or four.")
    if paragraphs and word_count(paragraphs[0]) > 80:
        faults.append(f"The first paragraph ||| First paragraph length ||| The first paragraph is {word_count(paragraphs[0])} words. The limit is 80.")
    return faults


def _em_dash_faults(section: str) -> list[str]:
    """House rules 4 and 7, checked here because the model cannot count: at most two em dashes
    in a section, and none in a heading."""
    faults = [f"{_strip(h)} ||| House rule 7 ||| The heading has an em dash."
              for h in re.findall(r"<h[1-6][^>]*>(.*?)</h[1-6]>", section, flags=re.I | re.S) if "\u2014" in h]
    count = _strip(section).count("\u2014")
    if count > 2:
        faults.append(f"The whole section ||| House rule 4 ||| The section has {count} em dashes. The limit is two.")
    return faults


def _check_section(section: str, system: str, fix_system: str, max_fixes: int, is_opening: bool = False,
                   find_prompt: str = FIND_RULE_BY_RULE_USER, fix_prompt: str = FIX_USER, progress=None) -> tuple[str, str, int]:
    """Check one section against the rules, correct it, and check again, up to max_fixes
    corrections, then stop. Returns (final section, record text, corrections made). With a
    `progress` file, each check and correction is saved to it as it finishes, and a stopped
    run resumes there."""
    find_prompt, fix_prompt = (p.replace("<<LOGIC>>", opening_logic_rules()) for p in (find_prompt, fix_prompt))
    saved = json.loads(progress.read_text()) if progress and progress.exists() else {}
    section = saved.get("section", section)
    record = saved.get("record", [f"### As written\n\n{section}\n"])
    fixes = saved.get("fixes", 0)
    faults = saved.get("faults")

    def save() -> None:
        if progress:
            progress.write_text(json.dumps({"section": section, "record": record, "fixes": fixes, "faults": faults}, indent=2))

    while True:
        if faults is None:
            result = structured_call(system=system, user=find_prompt.format(section_html=section), tool_name="report_faults",
                                     tool_description="Report the log and the faults.", input_schema=FIND_RULE_BY_RULE_SCHEMA, max_tokens=8000)
            found = result["faults"].strip()
            faults = [l for l in found.splitlines() if "|||" in l]
            counted = (_opening_count_faults(section) if is_opening else []) + _em_dash_faults(section)
            faults += counted
            record.append(f"### Check {fixes + 1}\n\n#### Rule by rule\n\n{result['log'].strip()}\n\n#### Faults\n\n{found}\n"
                          + ("\nCounted by the code:\n" + "\n".join(counted) + "\n" if counted else ""))
            save()
        if not faults or fixes >= max_fixes:
            break
        fixed = structured_call(system=fix_system, user=fix_prompt.format(faults="\n".join(faults), section_html=section), tool_name="submit_correction",
                                tool_description="Submit the corrected section.", input_schema=FIX_SCHEMA, max_tokens=16000)
        final = fixed["section_html"].strip() + "\n"
        left = [f for f in faults if _strip(f.split("|||")[0]) and _strip(f.split("|||")[0]) in _strip(final)]
        record.append(f"### Correction {fixes + 1}\n\n#### Fixer's draft\n\n{fixed['draft_html'].strip()}\n\n#### Fixer's check\n\n{fixed['check'].strip()}\n\n"
                      f"#### Corrected\n\n{final}\n" + (f"\nStill present after correction: {len(left)} of {len(faults)}\n" if left else ""))
        section = final
        fixes += 1
        faults = None
        save()
    return section, "\n".join(record), fixes


def brief_statistics(brief: str) -> str:
    """The Statistics section of a research brief, from its heading to the "## Unverified" after it, under the
    heading "## Research brief: statistics", for the checker and the fixer. The heading may be "## Statistics" or
    "**Statistics**". Empty when the brief has none."""
    start = re.search(r"^(?:#+ *|\*\*)Statistics\**\s*$", brief, re.M)
    if not start:
        return ""
    end = re.search(r"^(?:#+ *|\*\*)Unverified\**\s*$", brief[start.end():], re.M)
    section = brief[start.end():start.end() + end.start()] if end else brief[start.end():]
    return f"\n\n## Research brief: statistics\n\n{section.strip()}"


def _statistics_for(slug: str) -> str:
    """The statistics search's own output when research saved it; for an older brief, its Statistics section."""
    saved = ROOT / f"{slug}-output" / f"{slug}-statistics.md"
    if saved.exists() and saved.read_text().strip():
        return f"\n\n## Research brief: statistics\n\n{saved.read_text().strip()}"
    path = ROOT / f"{slug}-output" / f"{slug}-research.md"
    return brief_statistics(path.read_text()) if path.exists() else ""


def _brief(page) -> str:
    """The calendar's Article Brief / Angle, under the writer's "## Brief from the editor" heading, for the checkers and fixers."""
    return ("\n\n" + EDITOR_BRIEF.format(rationale=page.opportunity.rationale).strip()
            + "\n\nA sentence the brief from the editor gives word for word is the editor's own. Do not check it, and do not change it.")


def _system(template: str = REVIEW_SYSTEM) -> str:
    return template.format(reader=reader_rule(), transition=transition_rule(), section=section_rule(), items_in_a_set=items_in_a_set_rule(),
                                numbering=numbering_rule(), numbers=numbers_rules(), voice=voice_section(), tone=tone_section(),
                                elements_of_style=settings.elements_of_style())


def _save_body(page, body_html: str) -> None:
    content = page.content
    content.body_html = space_em_dashes(body_html)
    content.word_count = word_count(content.body_html)
    content.reading_time_minutes = reading_time(content.body_html)
    if os.environ.get("STAGE_TO_SANITY") == "true":   # files only unless asked; Sanity is for finished posts
        sanity.create_draft(content)
    _save_output(page)


def _write_record(page, record_name: str, title: str, records: list[str]) -> None:
    out = ROOT / f"{page.opportunity.id}-output" / record_name
    stamp = datetime.now().isoformat(timespec="minutes")
    out.write_text(f"# {title} {stamp}\n\n{usage_line()}\n\n" + "\n".join(records))


def _with_opening(prompt: str, logic: str, title: str) -> str:
    return prompt.replace("<<LOGIC>>", logic).replace("<<OPENING>>", opening_rules()).replace("<<TITLE>>", title)


def check_opening(slug: str, max_fixes: int = 6) -> None:
    """The opening's own check loop, with the opening's own checker and fixer. The body after the first <h2> is untouched.
    Each check and correction is saved to <slug>-opening-progress.json as it finishes, so a stopped run resumes there."""
    page = ContentPage.model_validate_json((ROOT / f"{slug}-output" / f"{slug}.json").read_text())
    sections = split_sections(page.content.body_html)
    if not _is_opening(sections[0]):
        log.warning(f"{slug} has no opening before its first H2; nothing to check")
        return
    progress = ROOT / f"{slug}-output" / f"{slug}-opening-progress.json"
    logic = opening_logic_rules()
    statistics = _statistics_for(slug)
    sections[0], record, fixes = _check_section(sections[0], _system() + statistics + _brief(page), _system(OPENING_FIX_SYSTEM) + statistics + _brief(page), max_fixes, is_opening=True,
                                                find_prompt=_with_opening(OPENING_FIND_USER, logic, page.content.h1),
                                                fix_prompt=_with_opening(OPENING_FIX_USER, logic, page.content.h1), progress=progress)
    _save_body(page, "".join(sections))
    _write_record(page, f"{slug}-opening-check.md", f"{slug} opening check", [f"## Opening\n\n{record}\n## Final\n\n{sections[0]}\n"])
    progress.unlink(missing_ok=True)
    log.info(f"Opening checked for {slug}: {fixes} correction(s)")


def check_post(slug: str, max_fixes: int = 4, workers: int = 4, stop_at: float = 0.0) -> bool:
    """The check loop on every section of the post except the opening, which has its own
    check (check_opening), `workers` sections at a time. A finished
    section is written to <slug>-check-progress.json at once, so a stopped run resumes
    there. Stops early, keeping the sections done, when `stop_at` dollars have been spent.
    Returns whether every section was checked."""
    page = ContentPage.model_validate_json((ROOT / f"{slug}-output" / f"{slug}.json").read_text())
    sections = split_sections(page.content.body_html)
    statistics = _statistics_for(slug)
    system, fix_system = _system() + statistics + _brief(page), _system(FIX_SYSTEM) + statistics + _brief(page)
    progress = ROOT / f"{slug}-output" / f"{slug}-check-progress.json"
    done: dict[str, dict] = {}
    if progress.exists():
        saved = json.loads(progress.read_text())
        if saved.get("section_count") == len(sections):
            done = saved["done"]
            log.info(f"Resuming {slug}: {len(done)}/{len(sections)} sections already checked")
    stopped = False
    skip = {0} if sections and _is_opening(sections[0]) else set()
    todo = [i for i in range(len(sections)) if str(i) not in done and i not in skip]
    for start in range(0, len(todo), workers):
        batch = todo[start:start + workers]
        with ThreadPoolExecutor(max_workers=len(batch)) as pool:
            results = list(pool.map(lambda i: _check_section(sections[i], system, fix_system, max_fixes), batch))
        for i, (final, record, fixes) in zip(batch, results):
            done[str(i)] = {"section": final, "record": record, "fixes": fixes}
            log.info(f"Section {i + 1}/{len(sections)} checked: {_section_name(sections[i])}, {fixes} correction(s)")
        progress.write_text(json.dumps({"section_count": len(sections), "done": done}, indent=2))
        log.info(f"Spent so far: {usage_line()}")
        if stop_at and cost() > stop_at and start + workers < len(todo):
            log.warning(f"Stopping {slug}: ${cost():.2f} spent, over the ${stop_at:.2f} limit; {len(done)}/{len(sections)} sections checked")
            stopped = True
            break
    records = []
    for i, section in enumerate(sections):
        if str(i) in done:
            sections[i] = done[str(i)]["section"]
            records.append(f"## {_section_name(section)}\n\n{done[str(i)]['record']}\n### Final\n\n{sections[i]}\n")
        elif i in skip:
            records.append("## Opening\n\nChecked separately by the opening check.\n")
        else:
            records.append(f"## {_section_name(section)}\n\nNot checked: the run stopped before this section.\n")
    _save_body(page, "".join(sections))
    _write_record(page, f"{slug}-check.md", f"{slug} check" + (" (stopped)" if stopped else ""), records)
    if not stopped:
        progress.unlink(missing_ok=True)
    log.info(f"Checked {slug}: {len(done)}/{len(sections)} sections; {usage_line()}")
    return not stopped


def _sentences(html: str) -> list[str]:
    """The plain-text sentences of a body, block by block."""
    text = re.sub(r"</(p|li|h[1-6]|td|th|blockquote)>|<br\s*/?>", "\n", html, flags=re.I)
    out = []
    for line in re.sub(r"<[^>]+>", "", text).splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            out += [s.strip() for s in re.split(r"(?:(?<=[.!?])|(?<=[.!?][\"”)]))\s+(?=[A-Z\"“\[])", line) if s.strip()]
    return out


def _restore_opening(opening: str, body_html: str) -> tuple[str, bool]:
    """The body with the original opening put back, if a fix changed it."""
    if not _is_opening(opening):
        return body_html, False
    sections = split_sections(body_html)
    if not _is_opening(sections[0]):
        return opening + body_html, True
    if _strip(sections[0]) != _strip(opening):
        sections[0] = opening
        return "".join(sections), True
    return body_html, False


def _faults(text: str) -> list[str]:
    return [l for l in text.splitlines() if "|||" in l]


def _none(text: str) -> str:
    """The text, or an empty string when the model wrote NONE."""
    text = text.strip()
    return "" if text.upper().rstrip(".") == "NONE" else text


def content_check(slug: str, stop_at: float = 0.0) -> bool:
    """The whole-article content check: one check of the whole article against the rules of
    the whole-article check, one fix with the fixer's self-check, then a review of only the
    changed sentences and the sentences around them, and one fix of what the review found.
    The checker reads the opening; the code puts the opening back if a fix touches it. A
    larger error a fixer reports is only reported: the code adds it to <slug>-larger-errors.md
    and the article carries on. Each step is saved to <slug>-content-progress.json, so a
    stopped run resumes. Returns whether the check finished."""
    page = ContentPage.model_validate_json((ROOT / f"{slug}-output" / f"{slug}.json").read_text())
    system = _system() + _brief(page)
    progress = ROOT / f"{slug}-output" / f"{slug}-content-progress.json"
    state = json.loads(progress.read_text()) if progress.exists() else {"step": "start", "body": page.content.body_html, "records": []}
    opening = split_sections(state.get("original", page.content.body_html))[0]
    state.setdefault("original", page.content.body_html)
    records = state["records"]

    def save(step: str, **kw) -> None:
        state.update(step=step, **kw)
        progress.write_text(json.dumps(state, indent=2))

    if state["step"] == "start":
        found = structured_call(system=system, user=CONTENT_FIND_USER.format(rules=CONTENT_RULES, body_html=state["body"]), tool_name="report_check",
                                tool_description="Report the log and the check.", input_schema=CONTENT_FIND_SCHEMA, max_tokens=16000)
        records.append(f"## Check of the whole article\n\n### Log\n\n{found['log'].strip()}\n\n### Check\n\n{found['check'].strip()}\n")
        save("found", faults=_none(found["check"]))
        log.info(f"Content check: {'faults found' if state['faults'] else 'no faults'} in {slug}; {usage_line()}")

    if state["step"] == "found":
        if not state["faults"]:
            save("done")
        else:
            fixed = structured_call(system=_system(CONTENT_FIX_SYSTEM) + _brief(page), user=CONTENT_FIX_USER.format(rules=CONTENT_RULES, fixes=CONTENT_FIXES, faults=state["faults"], body_html=state["body"]),
                                    tool_name="submit_article", tool_description="Submit the corrected article.", input_schema=CONTENT_FIX_SCHEMA, max_tokens=32000)
            body, restored = _restore_opening(opening, fixed["body_html"])
            before = set(_sentences(state["body"]))
            actual = [s for s in _sentences(body) if s not in before]
            listed = [l.strip() for l in fixed["changed"].splitlines() if l.strip()]
            missed = [s for s in actual if not any(s in l or l in s for l in listed)]
            larger = _none(fixed["larger_errors"])
            records.append(f"## Content fix\n\n### Changes\n\n{fixed['changes'].strip()}\n\n### Fixer's check\n\n{fixed['check'].strip()}\n\n"
                           f"### Larger errors\n\n{larger or 'None'}\n\n"
                           f"### Sentences the fixer listed\n\n" + "\n".join(listed) + "\n\n"
                           f"### Changed sentences the fixer did not list, found by the code\n\n" + ("\n".join(missed) or "None") + "\n"
                           + ("\nThe fix changed the opening. The code put the original opening back.\n" if restored else ""))
            _report_larger(slug, larger)
            save("fixed", body=body, changed=listed + missed)
            log.info(f"Content fixed in {slug}: {len(listed)} listed, {len(missed)} more found by the code; {usage_line()}")

    if state["step"] == "fixed" and stop_at and cost() > stop_at:
        log.warning(f"Stopping the content check for {slug}: ${cost():.2f} spent, over ${stop_at:.2f}; the review of the changes did not run")
    elif state["step"] == "fixed":
        review = structured_call(system=system, user=CONTENT_REVIEW_CHANGES_USER.format(rules=CONTENT_RULES, changed="\n".join(state["changed"]), body_html=state["body"]),
                                 tool_name="report_faults", tool_description="Report the log and the faults.", input_schema=FIND_RULE_BY_RULE_SCHEMA, max_tokens=16000)
        found = _faults(review["faults"])
        found += [f for s in split_sections(state["body"])[1:] for f in _em_dash_faults(s)]
        records.append(f"## Review of the changed sentences\n\n### Log\n\n{review['log'].strip()}\n\n### Faults\n\n{review['faults'].strip()}\n")
        if found:
            fixed = structured_call(system=_system(CONTENT_REVIEW_FIX_SYSTEM) + _brief(page), user=CONTENT_REVIEW_FIX_USER.format(rules=CONTENT_RULES, fixes=CONTENT_FIXES, faults="\n".join(found), body_html=state["body"]),
                                    tool_name="submit_article", tool_description="Submit the corrected article.", input_schema=CONTENT_FIX_SCHEMA, max_tokens=32000)
            body, restored = _restore_opening(opening, fixed["body_html"])
            larger = _none(fixed["larger_errors"])
            records.append(f"## Fix of what the review found\n\n### Changes\n\n{fixed['changes'].strip()}\n\n### Fixer's check\n\n{fixed['check'].strip()}\n\n"
                           f"### Larger errors\n\n{larger or 'None'}\n"
                           + ("\nThe fix changed the opening. The code put the original opening back.\n" if restored else ""))
            _report_larger(slug, larger)
            save("done", body=body)
        else:
            save("done")
        log.info(f"Content review for {slug}: {len(found)} fault(s); {usage_line()}")

    _save_body(page, state["body"])
    _write_record(page, f"{slug}-content-check.md", f"{slug} content check" + ("" if state["step"] == "done" else " (stopped)"),
                  records + [f"## Final\n\n{state['body']}\n"])
    if state["step"] == "done":
        progress.unlink(missing_ok=True)
    return state["step"] == "done"


def _report_larger(slug: str, larger: str) -> None:
    """Adds a larger error a fixer reported to <slug>-larger-errors.md. Only reported; nothing stops."""
    if not larger:
        return
    with (ROOT / f"{slug}-output" / f"{slug}-larger-errors.md").open("a") as f:
        f.write(f"{larger}\n\n")
    log.warning(f"Larger error reported in {slug}, added to {slug}-larger-errors.md; the article carries on")


def hide_resources(slug: str) -> None:
    """Replaces each resource in the article with a placeholder (lib.resources.hide), so no
    checker or fixer receives it, and saves the resources to <slug>-resources.json."""
    page = ContentPage.model_validate_json((ROOT / f"{slug}-output" / f"{slug}.json").read_text())
    body, found = res.hide(page.content.body_html)
    if not found:
        return
    (ROOT / f"{slug}-output" / f"{slug}-resources.json").write_text(json.dumps(found, indent=2))
    _save_body(page, body)
    log.info(f"Hid {len(found)} resource(s) in {slug} from the review steps")


def resource_review(slug: str) -> None:
    """Checks each resource only for consistency with the article: a resource must not contradict
    anything the article says or break any rule stated in the article. No sentence is checked, and
    a resource does not have to fit any pattern. A fixer corrects each resource with a direct
    contradiction. Then the resources go back in place of their placeholders. A resource whose
    placeholder a fixer removed goes back at the end of its section and is reported in
    <slug>-larger-errors.md. The record is <slug>-resource-review.md."""
    path = ROOT / f"{slug}-output" / f"{slug}-resources.json"
    if not path.exists():
        return
    page = ContentPage.model_validate_json((ROOT / f"{slug}-output" / f"{slug}.json").read_text())
    found = json.loads(path.read_text())
    article = page.content.body_html
    listed = "\n\n".join(f"### Resource {n}\n\n{res.inner(r['html'])}" for n, r in enumerate(found, 1))
    check = structured_call(system=RESOURCE_SYSTEM, user=RESOURCE_CHECK_USER.format(article=article, resources=listed), tool_name="report_faults",
                            tool_description="Report the faults in the resources.", input_schema=RESOURCE_CHECK_SCHEMA, max_tokens=8000)
    records = [f"## Check\n\n{json.dumps(check['faults'], indent=2)}\n"]
    for n, r in enumerate(found, 1):
        faults = [f for f in check["faults"] if f["resource"] == n]
        if not faults:
            continue
        listed_faults = "\n\n".join(f"Resource: {f['resource_quote']}\nArticle: {f['article_quote']}" for f in faults)
        fixed = structured_call(system=RESOURCE_SYSTEM, user=RESOURCE_FIX_USER.format(faults=listed_faults, resource=res.inner(r["html"]), article=article),
                                tool_name="submit_resource", tool_description="Submit the corrected resource.", input_schema=RESOURCE_FIX_SCHEMA, max_tokens=16000)
        r["html"] = f'<div class="resource">{fixed["resource_html"].strip()}</div>'
        records.append(f"## Resource {n}, corrected\n\n{r['html']}\n")
    body, missing = res.show(article, found)
    for n in missing:
        _report_larger(slug, f"A review fixer removed resource {n} from the section \"{found[n - 1]['section'] or 'the opening'}\". "
                             "The code put it back at the end of that section. Check that it is in the right place.")
    _save_body(page, body)
    path.unlink()
    _write_record(page, f"{slug}-resource-review.md", f"{slug} resource review", records)
    log.info(f"Resource review for {slug}: {len(check['faults'])} fault(s); {len(missing)} placeholder(s) missing")


def external_links(html: str) -> dict[str, list[str]]:
    """{website: [every URL in the article on that website]} for links to other websites."""
    from urllib.parse import urlparse
    found: dict[str, list[str]] = {}
    for href in re.findall(r'href="(https?://[^"]+)"', html):
        site = urlparse(href).netloc.lower().removeprefix("www.")
        if site and site != settings.site_domain.removeprefix("www."):
            found.setdefault(site, []).append(href)
    return found


def competitor_links(slug: str) -> None:
    """Lists the article's links to websites whose owners may sell hiring software, in
    <slug>-competitor-links.md, for the Fixes message in Slack, so they can be kept or removed by
    hand. The article is not changed."""
    page = ContentPage.model_validate_json((ROOT / f"{slug}-output" / f"{slug}.json").read_text())
    path = ROOT / f"{slug}-output" / f"{slug}-competitor-links.md"
    path.unlink(missing_ok=True)
    links = external_links(page.content.body_html)
    if not links:
        return
    result = structured_call(system=COMPETITOR_LINKS_SYSTEM, user=COMPETITOR_LINKS_USER.format(domains="\n".join(links)),
                             tool_name="report_competitors", tool_description="Report the websites whose owners sell hiring software.",
                             input_schema=COMPETITOR_LINKS_SCHEMA, max_tokens=4000)
    lines = [f"- {s['website']} ({s['company']}, {s['sells']}): " + ", ".join(links.get(s["website"].lower().removeprefix("www."), []))
             for s in result["suspects"]]
    if lines:
        path.write_text("\n".join(lines) + "\n")
    log.info(f"Competitor links in {slug}: {len(lines)} of {len(links)} website(s)")


def em_dash_report(slug: str) -> None:
    """The last step. The code counts the em dashes in every section (house rule 4) and looks
    for em dashes in headings (house rule 7), and lists what it finds in <slug>-em-dashes.md.
    No model call; the article is not changed."""
    page = ContentPage.model_validate_json((ROOT / f"{slug}-output" / f"{slug}.json").read_text())
    over = [f"- {_section_name(s)}: {f.split('|||')[-1].strip()}" for s in split_sections(res.without(page.content.body_html)) for f in _em_dash_faults(s)]
    if over:
        (ROOT / f"{slug}-output" / f"{slug}-em-dashes.md").write_text(f"# {slug}: sections over the em dash limit\n\n" + "\n".join(over) + "\n")
        log.warning(f"{len(over)} section(s) in {slug} over the em dash limit, listed in {slug}-em-dashes.md")
    else:
        log.info(f"No section in {slug} is over the em dash limit")


def transition_pass(slug: str, stop_at: float = 0.0) -> bool:
    """The whole-post transition pass: one check of every paragraph break and every section
    against the transition rule, one fix with the fixer's self-check, then a review of only
    the changed sentences and the sentences around them, and one fix of what the review found.
    The opening is never changed: the code puts it back if a fix touches it. Each step is
    saved to <slug>-transitions-progress.json, so a stopped run resumes after the last step.
    Returns whether the pass finished."""
    page = ContentPage.model_validate_json((ROOT / f"{slug}-output" / f"{slug}.json").read_text())
    system = _system() + _brief(page)
    progress = ROOT / f"{slug}-output" / f"{slug}-transitions-progress.json"
    state = json.loads(progress.read_text()) if progress.exists() else {"step": "start", "body": page.content.body_html, "records": []}
    opening = split_sections(state.get("original", page.content.body_html))[0]
    state.setdefault("original", page.content.body_html)
    records = state["records"]

    def save(step: str, **kw) -> None:
        state.update(step=step, **kw)
        progress.write_text(json.dumps(state, indent=2))

    if state["step"] == "start":
        found = structured_call(system=system, user=TRANSITIONS_FIND_USER.format(body_html=state["body"]), tool_name="report_faults",
                                tool_description="Report the log and the faults.", input_schema=TRANSITIONS_FIND_SCHEMA, max_tokens=16000)
        records.append(f"## Check of the whole post\n\n### Log\n\n{found['log'].strip()}\n\n### Faults\n\n{found['faults'].strip()}\n")
        save("found", faults=_faults(found["faults"]))
        log.info(f"Transitions: {len(state['faults'])} fault(s) in {slug}; {usage_line()}")

    if state["step"] == "found":
        if not state["faults"]:
            save("done")
        else:
            fixed = structured_call(system=_system(TRANSITIONS_FIX_SYSTEM) + _brief(page), user=TRANSITIONS_FIX_USER.format(faults="\n".join(state["faults"]), body_html=state["body"]),
                                    tool_name="submit_post", tool_description="Submit the corrected post.", input_schema=POST_FIX_SCHEMA, max_tokens=32000)
            body, restored = _restore_opening(opening, fixed["body_html"])
            before = set(_sentences(state["body"]))
            actual = [s for s in _sentences(body) if s not in before]
            listed = [l.strip() for l in fixed["changed"].splitlines() if l.strip()]
            missed = [s for s in actual if not any(s in l or l in s for l in listed)]
            records.append(f"## Transition fix\n\n### Changes\n\n{fixed['changes'].strip()}\n\n### Fixer's check\n\n{fixed['check'].strip()}\n\n"
                           f"### Sentences the fixer listed\n\n" + "\n".join(listed) + "\n\n"
                           f"### Changed sentences the fixer did not list, found by the code\n\n" + ("\n".join(missed) or "None") + "\n"
                           + ("\nThe fix changed the opening. The code put the original opening back.\n" if restored else ""))
            save("fixed", body=body, changed=listed + missed)
            log.info(f"Transitions fixed in {slug}: {len(listed)} listed, {len(missed)} more found by the code; {usage_line()}")

    if state["step"] == "fixed" and stop_at and cost() > stop_at:
        log.warning(f"Stopping the transition pass for {slug}: ${cost():.2f} spent, over ${stop_at:.2f}; the review of the changes did not run")
    elif state["step"] == "fixed":
        review = structured_call(system=system, user=REVIEW_CHANGES_USER.format(changed="\n".join(state["changed"]), body_html=state["body"]),
                                 tool_name="report_faults", tool_description="Report the log and the faults.", input_schema=FIND_RULE_BY_RULE_SCHEMA, max_tokens=16000)
        found = _faults(review["faults"])
        found += [f for s in split_sections(state["body"])[1:] for f in _em_dash_faults(s)]
        records.append(f"## Review of the changed sentences\n\n### Log\n\n{review['log'].strip()}\n\n### Faults\n\n{review['faults'].strip()}\n")
        if found:
            fixed = structured_call(system=_system(REVIEW_FIX_SYSTEM) + _brief(page), user=REVIEW_FIX_USER.format(faults="\n".join(found), body_html=state["body"]),
                                    tool_name="submit_post", tool_description="Submit the corrected post.", input_schema=POST_FIX_SCHEMA, max_tokens=32000)
            body, restored = _restore_opening(opening, fixed["body_html"])
            records.append(f"## Fix of what the review found\n\n### Changes\n\n{fixed['changes'].strip()}\n\n### Fixer's check\n\n{fixed['check'].strip()}\n"
                           + ("\nThe fix changed the opening. The code put the original opening back.\n" if restored else ""))
            save("done", body=body)
        else:
            save("done")
        log.info(f"Transition review for {slug}: {len(found)} fault(s); {usage_line()}")

    _save_body(page, state["body"])
    _write_record(page, f"{slug}-transitions.md", f"{slug} transition pass" + ("" if state["step"] == "done" else " (stopped)"),
                  records + [f"## Final\n\n{state['body']}\n"])
    if state["step"] == "done":
        progress.unlink(missing_ok=True)
    return state["step"] == "done"


if __name__ == "__main__":
    args = sys.argv[1:]
    commands = {"--check": check_post, "--check-opening": check_opening, "--content": content_check, "--transitions": transition_pass}
    if not args or args[0] not in commands:
        sys.exit(__doc__)
    for s in args[1:]:
        commands[args[0]](s)
