Usage
=====

Tools
-----

Command Line Utility
^^^^^^^^^^^^^^^^^^^^

Locally run ``make`` to print out the available options.

.. warning::
    The generated documentation contains sensitive information like the application configuration with passwords.

GPX to GeoJSON File Conversion
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Locally run ``togeojson myfile.gpx > myfile.geojson``

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

* Run ``make js-update``
* `jQuery <https://jquery.com/download/>`_
* `jQuery UI <https://jqueryui.com/download/>`_
* `Bootstrap with Popper <https://getbootstrap.com/>`_
* `OpenLayers <https://openlayers.org/>`_

.. warning::
    Updates may break the application so you should test before deploying.
