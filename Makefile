PYTHON ?= python3
PORT ?= 8000
DEV_PORT ?= 8766
PREVIEW_PORT ?= 8001
ADMIN_PORT ?= 8766
ADMIN_PROXY_PORT ?= 8082

.PHONY: help build dev admin start serve preview test validate

help:
	@printf '%s\n' \
		'make dev      Démarre le site avec actualisation automatique' \
		'make admin    Démarre le site et l’administration locale' \
		'make start    Génère et démarre le site' \
		'make build    Génère le site dans dist/' \
		'make preview  Génère les brouillons et les affiche' \
		'make test     Lance tous les tests' \
		'make dev DEV_PORT=8767  Utilise un autre port de développement' \
		'make start PORT=8080    Utilise un autre port statique'

build:
	$(PYTHON) tools/build-site.py --root .

dev:
	$(PYTHON) tools/dev-server.py --root . --port $(DEV_PORT)

admin:
	$(PYTHON) tools/admin-dev.py --root . --port $(ADMIN_PORT) --proxy-port $(ADMIN_PROXY_PORT)

start: build
	$(PYTHON) -m http.server $(PORT) --directory dist

serve: start

preview:
	$(PYTHON) tools/build-site.py --root . --output dist-preview --include-drafts
	$(PYTHON) -m http.server $(PREVIEW_PORT) --directory dist-preview

test:
	$(PYTHON) -m unittest tools/test_content_data.py tools/test_built_site.py tools/test_deploy.py -v

validate: build test
