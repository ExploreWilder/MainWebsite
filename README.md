# ExploreWilder

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg)](https://github.com/prettier/prettier) [![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/) [![Checked with mypy](https://camo.githubusercontent.com/34b3a249cd6502d0a521ab2f42c8830b7cfd03fa/687474703a2f2f7777772e6d7970792d6c616e672e6f72672f7374617469632f6d7970795f62616467652e737667)](https://mypy.readthedocs.io/en/stable/introduction.html "Mypy is an optional static type checker for Python") [![Under BSD-3-Clause](https://img.shields.io/github/license/explorewilder/mainwebsite)](https://github.com/ExploreWilder/MainWebsite/blob/master/LICENCE.md) ![CodeQL](https://github.com/ExploreWilder/MainWebsite/workflows/CodeQL/badge.svg)

## Demo

The project is my website: https://explorewilder.com/

It is currently hosted in a shared server running a virtual environment of Python 3.

## About

This is just an example of website using awesome open source technologies! The project was not created to be a template or a flexible CMS, but for my own use. Feel free to take whatever inspiration from it that you want. Here is a list of implemented features:

- [x] Asynchronous photo gallery
- [x] Hi-res photo viewer
- [x] Configurable multi-layer map viewers (2D and 3D) with interactive elevation profile
- [x] Show stories (markdown file and scrollytelling 2.5D map)
- [x] Likes without subscription – easy peasy lemon squeezy!
- [x] Social networks share buttons
- [x] Twitter and Mastodon timelines displayed without external requests
- [x] Contact and feedback forms
- [x] Exclusive access: restricted area and unlocked features
- [x] Emails (newsletter + account management)
- [x] Privacy friendly and GDPR compliant
- [x] Security focused
- [x] Web responsive and cross browser compatible
- [x] SEO optimisations
- [x] Ko-fi.com webhook integration
- [x] Admin space: manage the gallery, stories, members, see statistics (likes and views)

I used the following frameworks and tools:

### Server side:

* [Python 3](https://www.python.org/)
* [Flask](https://palletsprojects.com/p/flask/)
* [MySQL](https://www.mysql.com/)
* [Twitter API](https://developer.twitter.com/en) and [Mapbox Maps API](https://docs.mapbox.com/api/maps/)

### Client side:

* Compiled [Less](http://lesscss.org/)
* [HTML5](https://en.wikipedia.org/wiki/HTML5)
* [Fontawesome](https://fontawesome.com/)
* [JavaScript](https://en.wikipedia.org/wiki/JavaScript) with [JQuery](https://jquery.com/)
* [Bootstrap](https://getbootstrap.com/)
* [jQuery UI](https://jqueryui.com/)
* Dynamic maps with [OpenLayers](https://openlayers.org/), [Mapbox GL JS](https://docs.mapbox.com/mapbox-gl-js/overview/), and [VTS Browser JS](https://github.com/melowntech/vts-browser-js)
* Dynamic charts with [Chart.js](https://www.chartjs.org)

### Developer side:

* A bunch of free software
* [Tests](tests/) with [pytest](https://docs.pytest.org/en/latest/)
* [Mypy](https://mypy.readthedocs.io/en/stable/introduction.html "Mypy is an optional static type checker for Python"), [Pylint](https://pylint.pycqa.org/en/latest/intro.html "Pylint is a tool that checks for errors in Python code"), [Black](https://github.com/psf/black "Black is the uncompromising Python code formatter")
* [Sphinx](http://www.sphinx-doc.org/en/master/)
* [Sentry](https://sentry.io/)
* [Gulp](https://gulpjs.com/)

## Documentation

The documentation is in the [doc](doc/) directory.
