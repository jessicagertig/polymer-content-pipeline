from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Claude
    anthropic_api_key: str = ""

    # Google — the OAuth client and refresh token inflow-ats and polymer-engagement-pipeline
    # use for the internal sheets (same variable names). The token's grant is the
    # `spreadsheets` scope only; Search Console needs its own refresh token.
    google_internal_sheets_client_id: str = ""
    google_internal_sheets_client_secret: str = ""
    google_internal_sheets_refresh_token: str = ""
    google_search_console_refresh_token: str = ""   # empty = Google indexing requests are skipped
    ga4_property_id: str = ""
    gsc_site_url: str = "https://www.polymer.co/"

    # Sanity — dataset and token read the same variable names wrk-marketing's
    # web/.env.local defines, so that file can be sourced as-is.
    sanity_project_id: str = "a6d1clb1"
    sanity_dataset: str = Field("", validation_alias=AliasChoices("SANITY_DATASET", "SANITY_STUDIO_API_DATASET"))
    sanity_api_version: str = "2021-03-25"
    sanity_api_token: str = Field("", validation_alias=AliasChoices("SANITY_API_TOKEN", "SANITY_API_WRITE_TOKEN"))
    sanity_author_ref: str = "author-jessica-gertig"
    sanity_studio_url: str = ""   # Studio base URL, for the draft link in Slack; empty = no link

    # IndexNow — the key must also be hosted at https://<site_domain>/<key>.txt
    indexnow_key: str = ""

    # Slack
    slack_bot_token: str = ""
    slack_content_channel: str = ""
    slack_alerts_channel: str = ""
    slack_report_channel: str = ""   # run reports; falls back to content channel if empty

    # Behavior
    max_opportunities_per_run: int = 10
    min_search_volume: int = 100
    auto_generate_on_approval: bool = True
    site_domain: str = "www.polymer.co"
    research_max_searches: int = 5   # web searches per post (the web search tool's max_uses)
    research_step_searches: int = 6  # web searches across the three research calls (definitions, topic, statistics)
    research_max_tokens: int = 3000  # max_tokens on each research response
    research_max_words: int = 1000   # length of the brief the researcher is asked for
    research_reuse: bool = False     # reuse a saved <slug>-output/<slug>-research.md instead of searching (a -vN slug reuses the base post's)

    # GitHub — the Lambda commits each run's output (<slug>-output/ and the calendar CSV)
    # to this repo. A run on a laptop writes into the checkout and never pushes.
    github_repo: str = ""            # "owner/name"
    github_token: str = ""           # fine-grained PAT for that repo: Contents read and write
    github_branch: str = "main"

    def brand_guidelines(self) -> str:
        """The writing guide. The house rules are written into the prompt itself (prompts/content.py); config/house-rules.md is the record of them."""
        here = Path(__file__).parent
        return (here / "brand_guidelines.md").read_text() if (here / "brand_guidelines.md").exists() else ""

    def elements_of_style(self) -> str:
        """Strunk's The Elements of Style (1918, public domain), sent in the writer's system prompt."""
        path = Path(__file__).parent / "elements-of-style.md"
        return path.read_text() if path.exists() else ""

    def feature_inventory(self) -> str:
        path = Path(__file__).parent / "polymer-feature-inventory.md"
        return path.read_text() if path.exists() else ""

    def alternatives_playbook(self) -> str:
        """The outline for the alternatives format: the playbook, then the positioning guidelines it cites."""
        here = Path(__file__).parent
        parts = [here / "alternatives-playbook.md", here / "polymer-competitive-positioning.md"]
        return "\n\n".join(p.read_text() for p in parts if p.exists())

    def competitor_domains(self) -> list[str]:
        """Competitor domains the researcher's web search never returns results from."""
        path = Path(__file__).parent / "competitor-domains.txt"
        return [line.strip() for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


settings = Settings()
