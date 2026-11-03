"""Resources in an article: email templates, job description templates, rubrics. The writer puts
each one in <div class="resource">. No review step receives them: hide() replaces each one with a
placeholder once the article is written, and show() puts them back after the transition pass, for
the resource review (review_post.resource_review). unwrap() removes the wrappers before the article
is staged to Sanity.
"""

import re

# ponytail: a resource ends at its first </div>; the writer is told not to put another div inside one.
RESOURCE = re.compile(r'<div class="resource">(.*?)</div>', re.S | re.I)
H2 = re.compile(r"<h2[^>]*>(.*?)</h2>", re.S | re.I)


def placeholder(n: int) -> str:
    return f'<div data-resource="{n}"></div>'


def hide(html: str) -> tuple[str, list[dict]]:
    """Returns the article with resource N replaced by placeholder(N), and the resources in order,
    each with the H2 heading of the section it was in."""
    resources = []

    def swap(m: re.Match) -> str:
        heads = H2.findall(html, 0, m.start())
        resources.append({"html": m.group(0), "section": heads[-1] if heads else ""})
        return placeholder(len(resources))

    return RESOURCE.sub(swap, html), resources


def show(html: str, resources: list[dict]) -> tuple[str, list[int]]:
    """Puts each resource back in place of its placeholder. Returns the article and the numbers of
    the resources whose placeholder was missing: each of those goes at the end of the section it
    was in, or at the end of the article when that heading is gone."""
    missing = []
    for n, r in enumerate(resources, 1):
        mark = placeholder(n)
        if mark in html:
            html = html.replace(mark, r["html"], 1).replace(mark, "")
            continue
        missing.append(n)
        head = next((m for m in H2.finditer(html) if m.group(1) == r["section"]), None)
        nxt = re.compile(r"<h2[\s>]", re.I).search(html, head.end()) if head else None
        at = nxt.start() if nxt else len(html)
        html = html[:at] + r["html"] + html[at:]
    return html, missing


def inner(resource_html: str) -> str:
    return RESOURCE.sub(r"\1", resource_html).strip()


def unwrap(html: str) -> str:
    return RESOURCE.sub(r"\1", html)


def without(html: str) -> str:
    return RESOURCE.sub("", html)

