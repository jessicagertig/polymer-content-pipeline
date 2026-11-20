import requests

import review_post
from models.content import ContentOpportunity, ContentPage, GeneratedContent, PageType


class _Response:
    def __init__(self, status_code, url):
        self.status_code, self.url = status_code, url

    def close(self):
        pass


def test_a_link_is_dead_when_missing_unanswered_or_sent_to_the_home_page(monkeypatch):
    pages = {"https://a.com/gone": _Response(404, "https://a.com/gone"),
             "https://a.com/moved": _Response(200, "https://a.com/"),
             "https://a.com/blocked": _Response(403, "https://a.com/blocked"),
             "https://a.com/fine": _Response(200, "https://a.com/articles/fine")}

    def get(url, **kwargs):
        if url == "https://nowhere.invalid/x":
            raise requests.exceptions.ConnectionError()
        return pages[url]

    monkeypatch.setattr(requests, "get", get)
    assert [review_post.load_link(u) for u in pages] == ["dead", "dead", "HTTP 403", "ok"]
    assert review_post.load_link("https://nowhere.invalid/x") == "dead"


def test_the_link_check_lists_dead_and_unloaded_links_and_leaves_the_article_alone(tmp_path, monkeypatch):
    monkeypatch.setattr(review_post, "ROOT", tmp_path)
    (tmp_path / "post-output").mkdir()
    body = ('<p>One <a href="https://a.com/gone">study</a>.</p><p>Two <a href="https://b.com/x">survey</a>.</p>'
            '<p>Three <a href="https://c.com/y">report</a>.</p>')
    opp = ContentOpportunity(id="post", page_type=PageType.GUIDE, keyword="k", proposed_url="/blog/post", proposed_title="T", rationale="r")
    saved = ContentPage(opportunity=opp, content=GeneratedContent(title="T", h1="T", meta_description="m", slug="post", body_html=body))
    (tmp_path / "post-output" / "post.json").write_text(saved.model_dump_json())
    status = {"https://a.com/gone": "dead", "https://b.com/x": "HTTP 403", "https://c.com/y": "ok"}
    monkeypatch.setattr(review_post, "load_link", status.get)
    searched = []
    monkeypatch.setattr(review_post, "suggest_replacement", lambda url, paragraph: searched.append(paragraph) or "https://a.com/new")

    review_post.link_check("post")

    listed = (tmp_path / "post-output" / "post-links.md").read_text()
    assert "- <https://a.com/gone>, suggested replacement: <https://a.com/new>" in listed
    assert "- <https://b.com/x> (HTTP 403)" in listed and "c.com" not in listed
    assert searched == ["One study."]   # no search for a link that could not be loaded
    assert (tmp_path / "post-output" / "post.json").read_text() == saved.model_dump_json()
