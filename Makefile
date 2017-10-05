PROJECT_NAME = tracpro
STATIC_LIBS_DIR = ./$(PROJECT_NAME)/static/libs

default: lint test

test:
	# Run all tests and report coverage
	# Requires coverage
	coverage erase
	coverage run manage.py test --keepdb
	coverage report -m --fail-under 80

lint-py:
	# Check for Python formatting issues
	# Requires flake8
	flake8 .

lint-js:
	# Check JS for any problems
	# Requires jshint
	find -name "*.js" -not -path "${STATIC_LIBS_DIR}*" -a -not -path "./tracpro/static/js/*" -print0 | xargs -0 jshint

lint: lint-py lint-js

$(STATIC_LIBS_DIR):
	mkdir -p $@

update-static-libs: $(LIBS)

# Generate a random string of desired length
generate-secret: length = 32
generate-secret:
	@strings /dev/urandom | grep -o '[[:alnum:]]' | head -n $(length) | tr -d '\n'; echo

conf/%.pub.ssh:
	# Generate SSH deploy key for a given environment
	ssh-keygen -t rsa -b 4096 -f $*.priv -C "$*@${PROJECT_NAME}"
	@mv $*.priv.pub $@

staging-deploy-key: conf/staging.pub.ssh

production-deploy-key: conf/production.pub.ssh

# Translation helpers
makemessages:
	# Extract English messages from our source code
	python manage.py makemessages --ignore 'conf/*' --ignore 'docs/*' --ignore 'requirements/*' \
		--no-location --no-obsolete -l en

compilemessages:
	# Compile PO files into the MO files that Django will use at runtime
	python manage.py compilemessages

pushmessages:
	# Upload the latest English PO file to Transifex
	tx push -s

pullmessages:
	# Pull the latest translated PO files from Transifex
	tx pull -af

setup:
	virtualenv -p `which python2.7` $(WORKON_HOME)/tracpro
	$(WORKON_HOME)/tracpro/bin/pip install -U pip wheel
	$(WORKON_HOME)/tracpro/bin/pip install -Ur requirements/dev.txt
	$(WORKON_HOME)/tracpro/bin/pip freeze
	npm install
	npm update
	cp tracpro/settings/local.example.py tracpro/settings/local.py
	echo "DJANGO_SETTINGS_MODULE=tracpro.settings.local" > .env
	createdb -E UTF-8 tracpro
	$(WORKON_HOME)/tracpro/bin/python manage.py migrate
	if [ -e project.travis.yml ] ; then mv project.travis.yml .travis.yml; fi
	@echo
	@echo "The tracpro project is now setup on your machine."
	@echo "Run the following commands to activate the virtual environment and run the"
	@echo "development server:"
	@echo
	@echo "	workon tracpro"
	@echo "	npm run dev"

update:
	$(WORKON_HOME)/tracpro/bin/pip install -U -r requirements/dev.txt
	npm install
	npm update

# Build documentation
docs:
	cd docs && make html

.PHONY: default test lint lint-py lint-js generate-secret makemessages \
		pushmessages pullmessages compilemessages docs

.PRECIOUS: conf/%.pub.ssh
