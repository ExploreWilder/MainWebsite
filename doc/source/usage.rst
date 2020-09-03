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
    That will run gulp in the background, on startup and every time you change a JS or Less file in the static directory (but not in subdirectories).

GPX to GeoJSON file conversion
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Locally run ``togeojson myfile.gpx > myfile.geojson``

Find out the number of lines of code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Locally run ``./utils.sh cloc``

Generate this documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Locally run ``./utils.sh doc-localhost``

.. warning::
    The documentation contains sensitive constants and code fragments (f.i. passwords) so please remove the sensitive information before generating the documentation or keep the doc secret.

Test the application
^^^^^^^^^^^^^^^^^^^^

Run ``./utils.sh test-localhost``

Test and generate test report
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run ``./utils.sh test-coverage-localhost``

Import/Export the MySQL Database
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

Run:

.. code-block:: none

    pip install --upgrade pip
    pip install --use-feature=2020-resolver -r requirements.txt -U

JavaScript / CSS / Fonts
^^^^^^^^^^^^^^^^^^^^^^^^

Check version and download:

* `jQuery <https://jquery.com/download/>`_
* `jQuery UI <https://jqueryui.com/download/>`_
* `jQuery Zoom <https://github.com/jackmoore/zoom>`_
* Fontawesome: ``cd flaskr/static && npm install --save @fortawesome/fontawesome-free``
* `Bootstrap with Popper <https://getbootstrap.com/>`_
* `Sentry <https://docs.sentry.io/error-reporting/quickstart/?platform=browser>`_
* `OpenLayers <https://openlayers.org/>`_
* `Chart.js with Moment.js <https://cdnjs.com/libraries/Chart.js>`_
* `Marked <https://github.com/markedjs/marked>`_
* `Mapbox GL JS <https://docs.mapbox.com/mapbox-gl-js/api/>`_
* `Intersection Observer <https://github.com/w3c/IntersectionObserver>`_
* `Scrollama <https://github.com/russellgoldenberg/scrollama>`_
* `tiff.js <https://github.com/seikichi/tiff.js>`_
* `lz-string <https://github.com/pieroxy/lz-string>`_

.. note::
    Updates may break the application so you should test before deploy.
