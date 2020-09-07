#!/bin/bash

prod_db_user="UNDISCLOSED"
prod_db_name="UNDISCLOSED"
prod_db_backup_dir=UNDISCLOSED

tool="${1}"
case ${tool} in
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
        gulp
        cd - >/dev/null
        ;;
    cloc)
        ls -1 *.sh *.py flaskr/*.py flaskr/*.sql flaskr/static/app/scripts/*.js \
            flaskr/static/app/styles/*.less flaskr/templates/*.html tests/*.py \
            tests/*.sql > cloc_files.txt
        cloc --list-file=cloc_files.txt
        rm cloc_files.txt
        ;;
    doc-localhost)
        source venv/bin/activate
        cd doc
        make clean
        make html
        echo "Open file: file://${PWD}/build/html/index.html"
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
    *)
        echo "`basename ${0}`:usage: [init-db-localhost]" \
            " | [backup-db-prod]" \
            " | [run-gulp]" \
            " | [cloc]" \
            " | [doc-localhost]" \
            " | [run-app-localhost]" \
            " | [test-coverage-localhost]" \
            " | [test-localhost]"
        exit 1
        ;;
esac
