# Polymer Blog Bot
# Usage:
#   make run          Scheduled run: drain Launch Batch, then stage this week's calendar post
#   make calendar N=2 Stage the next N scheduled calendar posts (default 1)
#   make launch       Stage every pending Launch Batch post
#   make index        Submit sitemap URLs modified in the last 24h to IndexNow + Google
#   make doctor       Check settings + connectivity
#   make test         Run the tests
#   make deploy       sam build && sam deploy (sources secrets from .env)

PYTHON := .venv/bin/python
N ?= 1

.PHONY: run calendar launch index doctor test deploy help

all: help

run:
	@set -a && . ./.env && set +a && $(PYTHON) main.py run

calendar:
	@set -a && . ./.env && set +a && $(PYTHON) main.py calendar $(N)

launch:
	@set -a && . ./.env && set +a && $(PYTHON) main.py launch

index:
	@set -a && . ./.env && set +a && $(PYTHON) main.py index

doctor:
	@set -a && . ./.env && set +a && $(PYTHON) main.py doctor

test:
	$(PYTHON) -m pytest tests

## Build and deploy the Lambda stack (sources secrets from .env)
deploy:
	@set -a && . ./.env && set +a && \
	sam build && sam deploy \
		--parameter-overrides \
		"AnthropicApiKey=$$ANTHROPIC_API_KEY" \
		"SanityDataset=$$SANITY_STUDIO_API_DATASET" \
		"SanityApiToken=$$SANITY_API_WRITE_TOKEN" \
		"SanityStudioUrl=$$SANITY_STUDIO_URL" \
		"SlackBotToken=$$SLACK_BOT_TOKEN" \
		"SlackContentChannel=$$SLACK_CONTENT_CHANNEL" \
		"GoogleInternalSheetsClientId=$$GOOGLE_INTERNAL_SHEETS_CLIENT_ID" \
		"GoogleInternalSheetsClientSecret=$$GOOGLE_INTERNAL_SHEETS_CLIENT_SECRET" \
		"GoogleInternalSheetsRefreshToken=$$GOOGLE_INTERNAL_SHEETS_REFRESH_TOKEN" \
		"GoogleSearchConsoleRefreshToken=$$GOOGLE_SEARCH_CONSOLE_REFRESH_TOKEN" \
		"GscSiteUrl=$$GSC_SITE_URL" \
		"IndexNowKey=$$INDEXNOW_KEY" \
		"GithubRepo=$$GITHUB_REPO" \
		"GithubToken=$$GITHUB_TOKEN"

help:
	@echo ""
	@echo "Polymer Blog Bot"
	@echo "================"
	@echo "  make run          Scheduled run (Launch Batch, then one calendar post)"
	@echo "  make calendar N=2 Stage the next N scheduled calendar posts"
	@echo "  make launch       Stage every pending Launch Batch post"
	@echo "  make index        Submit recently modified sitemap URLs for indexing"
	@echo "  make doctor       Check settings + connectivity"
	@echo "  make test         Run the tests"
	@echo "  make deploy       sam build && sam deploy"
	@echo ""
