# Polymer Blog Bot
# Usage:
#   make run          Scheduled run: drain Launch Batch, then stage this week's calendar post
#   make calendar N=2 Stage the next N scheduled calendar posts (default 1)
#   make launch       Stage every pending Launch Batch post
#   make index        Submit sitemap URLs modified in the last 24h to IndexNow + Google
#   make doctor       Check settings + connectivity
#   make test         Run the tests
#   make deploy       Deploy the Slack button Lambda (sources secrets from .env)

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

## Build and deploy the Slack Lambda (sources secrets from .env)
deploy:
	@set -a && . ./.env && set +a && \
	sam build && sam deploy \
		--parameter-overrides \
		"SlackBotToken=$$SLACK_BOT_TOKEN" \
		"SlackSigningSecret=$$SLACK_SIGNING_SECRET" \
		"SlackChannelId=$$SLACK_CONTENT_CHANNEL" \
		"GitHubToken=$$GITHUB_TOKEN"

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
	@echo "  make deploy       Deploy the Slack button Lambda"
	@echo ""
