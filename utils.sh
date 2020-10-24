#!/bin/bash

prod_db_user="UNDISCLOSED"
prod_db_name="UNDISCLOSED"
prod_db_backup_dir=UNDISCLOSED
export SENTRY_AUTH_TOKEN=UNDISCLOSED
export SENTRY_ORG=UNDISCLOSED

shopt -s expand_aliases
alias sentry-cli="./flaskr/static/node_modules/.bin/sentry-cli"
tool="${1}"
case ${tool} in
    sentry-release)
        VERSION=$(sentry-cli releases propose-version)
        echo "Release version: $VERSION"
        sentry-cli releases new --finalize -p flask $VERSION # Create a release
        sentry-cli releases set-commits --auto $VERSION # Associate commits with the release
        ;;
    init-db-localhost)
        source venv/bin/activate
        export FLASK_APP=flaskr
        export FLASK_ENV=development
        flask init-db
        deactivate
        ;;
    backup-db-prod)
        printf -v date '%(%Y-%m-%d)T' -1
        backup_file=backup_${date}.sql
        echo "Backup database..."
        mysqldump -u ${prod_db_user} ${prod_db_name} -r ${prod_db_backup_dir}/${backup_file} -v &&
        echo "Backup saved in ${backup_file}"
        ;;
    run-gulp)
        cd flaskr/static
        gulp ${2}
        cd - >/dev/null
        ;;
    cloc)
        ls -1 *.sh *.py flaskr/*.py flaskr/*.sql flaskr/static/app/scripts/*.js \
            flaskr/static/app/styles/*.less flaskr/templates/*.html tests/*.py \
            tests/*.sql flaskr/static/app/scripts/map_player_config/*.json \
            flaskr/static/*.js > cloc_files.txt
        cloc --list-file=cloc_files.txt
        rm cloc_files.txt
        ;;
    doc-localhost)
        source venv/bin/activate
        cd doc
        case ${2} in
            checklinks)
                make checklinks
                ;;
            *)
                make clean
                make html
                echo "Open file: file://${PWD}/build/html/index.html"
                ;;
        esac
        cd - >/dev/null
        deactivate
        ;;
    run-app-localhost)
        source venv/bin/activate
        export FLASK_APP=flaskr
        export FLASK_ENV=development
        flask run
        deactivate
        ;;
    test-coverage-localhost)
        source venv/bin/activate
        cd tests
        export FLASK_DEBUG=True
        coverage run -m pytest
        coverage html --include="../flaskr/*" --directory="../doc/htmlcov"
        echo "Open file: file://${PWD}/../doc/htmlcov/index.html"
        cd - >/dev/null
        deactivate
        ;;
    test-localhost)
        source venv/bin/activate
        cd tests
        export FLASK_DEBUG=True
        pytest #--setup-show
        cd - >/dev/null
        deactivate
        ;;
    mypy)
        source venv/bin/activate
        mypy --config-file mypy.ini flaskr/
        deactivate
        ;;
    black)
        source venv/bin/activate
        black flaskr/
        black tests/
        deactivate
        ;;
    isort)
        source venv/bin/activate
        # isort documentation:
        # https://github.com/PyCQA/isort/wiki/isort-Settings
        isort flaskr/ --force-single-line
        deactivate
        ;;
    pylint)
        source venv/bin/activate
        pylint flaskr/ --disable=unused-wildcard-import,wildcard-import,R0801 --extension-pkg-whitelist=pyquadkey2.tilesystem
        deactivate
        ;;
    *)
        echo "`basename ${0}`:usage: [sentry-release]" \
            "| [init-db-localhost]" \
            "| [backup-db-prod]" \
            "| [run-gulp (run-all)]" \
            "| [cloc]" \
            "| [doc-localhost]" \
            "| [run-app-localhost]" \
            "| [test-coverage-localhost]" \
            "| [test-localhost]" \
            "| [mypy]" \
            "| [black]" \
            "| [isort]" \
            "| [pylint]"
        exit 1
        ;;
esac
