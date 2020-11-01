Usage
=====

The script *utils.sh* activates the venv so you don't have to do anything before or after using it, except starting and stopping the MySQL deamon.

Run the App Locally
-------------------

As simple as ``./utils.sh run-app-localhost``. Log is in the standard output.

The website should be available in this address: http://127.0.0.1:5000/

Tools
-----

Compile the JavaScript and Less files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Locally run ``./utils.sh run-gulp``

.. note::
    That will run gulp in the background every time you change a JS or Less file in the static directory (but not in subdirectories). If you want to run all Gulp tasks, run ``./utils.sh run-gulp run-all``

GPX to GeoJSON File Conversion
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Locally run ``togeojson myfile.gpx > myfile.geojson``

Find Out The Number of Lines of Code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Locally run ``./utils.sh cloc``

Generate This Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Locally run ``./utils.sh doc-localhost``

.. warning::
    The documentation contains sensitive constants and code fragments (f.i. passwords) so please remove the sensitive information before generating the documentation or keep the doc secret.

.. note::
    The command ``./utils.sh doc-localhost checklinks`` will `test <https://sublime-and-sphinx-guide.readthedocs.io/en/latest/references.html#test-external-links>`_ all external links in the documentation.

Test The Application
^^^^^^^^^^^^^^^^^^^^

Run ``./utils.sh test-localhost``

Test and Generate Test Report
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run ``./utils.sh test-coverage-localhost``

Import/Export The MySQL Database
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Import your database locally:
  ``mysql -u root -p clement1_main < clement1_main_backup.sql``
* Import your database in prod:
  ``mysql -u username -p databasename < clement1_main_backup.sql``
* Backup your database:
  ``mysqldump -u username -p databasename -r clement1_main_backup.sql``

Updates
-------

Python
^^^^^^

Run: ``make py-update``

JavaScript / CSS / Fonts
^^^^^^^^^^^^^^^^^^^^^^^^

Check version and download:

* ``cd flaskr/static && npm update --dev``
* `jQuery <https://jquery.com/download/>`_
* `jQuery UI <https://jqueryui.com/download/>`_
* `Bootstrap with Popper <https://getbootstrap.com/>`_
* `OpenLayers <https://openlayers.org/>`_

.. note::
    Updates may break the application so you should test before deploying.
