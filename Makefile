VENV_NAME   ?=venv
VENV_ACTIVATE=. ${VENV_NAME}/bin/activate
PYTHON       =${VENV_NAME}/bin/python3
PYLINT_FLAGS =--disable=unused-wildcard-import,wildcard-import,line-too-long,R0801 --extension-pkg-whitelist=pyquadkey2.tilesystem
SPHINX_FLAGS =SPHINXBUILD="../${PYTHON} -m sphinx"
SENTRY_CLI   =./flaskr/static/node_modules/.bin/sentry-cli
GIT_VERSION  =`${SENTRY_CLI} releases propose-version`
PY_REQ       =require_dev.txt requirements.txt
CONFIG_FILE :=Makefile.config

ifeq ($(wildcard $(CONFIG_FILE)),)
$(error $(CONFIG_FILE) not found. See $(CONFIG_FILE).example)
endif
include $(CONFIG_FILE)

.PHONY: help mypy pylint check isort black prettier format test coverage run doc \
		doc-checklinks cloc gulp dist git-hash commit push push-force reset \
		ssh py-update js-update touch-books

.DEFAULT: help
help:
	@echo ""
	@echo "Welcome to the ExploreWilder project!$B 🤠"
	@echo ""
	@echo "What would you like to do?"
	@echo ""
	@echo ",~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~."
	@echo "| make mypy ----------→ check type annotations with mypy.                                      |"
	@echo "| make pylint --------→ lint with pylint.                                                      |"
	@echo "| make check ---------→ check type annotations with mypy and lint with pylint.                 |"
	@echo "| make isort ---------→ sort Python imports.                                                   |"
	@echo "| make black ---------→ format the Python project.                                             |"
	@echo "| make prettier ------→ format the JavaScript project.                                         |"
	@echo "| make format --------→ sort Python imports and format the Python & JavaScript projects.       |"
	@echo "| make test ----------→ test the Python project with pytest.                                   |"
	@echo "| make coverage ------→ test coverage of the Python project.                                   |"
	@echo "| make run -----------→ run the app on http://127.0.0.1:5000/ (press CTRL+C to quit).          |"
	@echo "| make doc -----------→ generate the documentation with Sphinx.                                |"
	@echo "| make doc-checklinks → generate and check links of the documentation.                         |"
	@echo "| make cloc ----------→ count the lines of code.                                               |"
	@echo "| make gulp ----------→ run the Gulp daemon (press CTRL+C to quit).                            |"
	@echo "| make dist ----------→ build all scripts with Gulp and run the daemon (press CTRL+C to quit). |"
	@echo "| make git-hash ------→ print out the Git SHA1 of the last commit.                             |"
	@echo "| make commit --------→ format, check, test, generate the documentation, and finally commit.   |"
	@echo "| make push ----------→ push the local repo and release the commit to Sentry.                  |"
	@echo "| make push-force ----→ force push the local repo and release the commit to Sentry.            |"
	@echo "| make reset ---------→ initialise the database.                                               |"
	@echo "| make ssh -----------→ connect to the server with SSH.                                        |"
	@echo "| make py-update -----→ update pip and all Python dependencies (dev+prod).                     |"
	@echo "| make js-update -----→ update all JavaScript dependencies (dev+prod), and run 'make dist'.    |"
	@echo "| make touch-books ---→ force update the Markdown stories and static maps.                     |"
	@echo "'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'"
	@echo ""
	@echo "Any trouble? 🤔 Please raise an issue on GitHub: ${GIT_REPO}"
	@echo ""

venv: ${VENV_NAME}/bin/activate

mypy: venv
	${PYTHON} -m mypy --config-file mypy.ini flaskr/

pylint: venv
	${PYTHON} -m pylint flaskr/ ${PYLINT_FLAGS} || true

check: mypy pylint

# documentation: https://github.com/PyCQA/isort/wiki/isort-Settings
isort: venv
	${PYTHON} -m isort flaskr/ --force-single-line
	${PYTHON} -m isort tests/ --force-single-line

black: venv
	${PYTHON} -m black flaskr/
	${PYTHON} -m black tests/

prettier:
	@cd flaskr/static && \
	npm run prettier

format: isort black prettier

# for debug purpose, add the --setup-show flag to pytest
test: venv
	@cd tests && \
	export FLASK_DEBUG=True && \
	../${PYTHON} -m pytest --capture=tee-sys

coverage: venv
	@cd tests && \
	export FLASK_DEBUG=True && \
	../${PYTHON} -m coverage run -m pytest && \
	../${PYTHON} -m coverage html --include="../flaskr/*" --directory="../doc/htmlcov" && \
	../${PYTHON} -m coverage json --include="../flaskr/*" && \
	../${PYTHON} coverage_to_readme.py && \
	rm coverage.json
	@echo "Open file: file://${PWD}/doc/htmlcov/index.html"

run: venv
	@export FLASK_APP=flaskr && \
    export FLASK_ENV=development && \
    ${PYTHON} -m flask run

doc: venv
	@cd doc && \
	make clean ${SPHINX_FLAGS} && make html ${SPHINX_FLAGS}
	@echo "Open file: file://${PWD}/doc/build/html/index.html"

doc-checklinks: venv
	@cd doc && \
	make checklinks ${SPHINX_FLAGS}

cloc:
	@ls -1 *.sh *.py flaskr/*.py flaskr/*.sql flaskr/static/app/scripts/*.js \
            flaskr/static/app/styles/*.less flaskr/templates/*.html tests/*.py \
            tests/*.sql flaskr/static/app/scripts/map_player_config/*.json \
            flaskr/static/*.js Makefile > cloc_files.txt && \
    cloc --list-file=cloc_files.txt && \
    rm cloc_files.txt

gulp:
	@cd flaskr/static && \
	gulp --no-color

dist:
	@cd flaskr/static && \
	gulp build --no-color

git-hash:
	@echo "Release version: ${GIT_VERSION} 🚀"

# signed commit
commit: format check coverage doc
	@git commit -S

# create a Sentry release and associate commits with the release
push:
	@git push && \
	${SENTRY_CLI} releases new --finalize -p flask ${GIT_VERSION} && \
	${SENTRY_CLI} releases set-commits --auto ${GIT_VERSION}

push-force:
	@git push -f && \
	${SENTRY_CLI} releases new --finalize -p flask ${GIT_VERSION} && \
	${SENTRY_CLI} releases set-commits --auto ${GIT_VERSION}

reset: venv
	@export FLASK_APP=flaskr && \
	export FLASK_ENV=development && \
	${PYTHON} -m flask init-db

ssh:
	@ssh -p ${SERVER_PORT} ${SERVER_ADDR}

py-update: venv
	@pip install --upgrade pip && \
	${foreach file, ${PY_REQ}, pip install -r ${file} -U}

js-update:
	@cd flaskr/static && \
	npm update --dev
	@make dist

touch-books:
	@find books/ -type f -name "*.md" -exec touch {} +
	@find books/ -type f -name "*.gpx_static_map.*" -exec rm {} +
