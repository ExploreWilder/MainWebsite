
import os
import sys


sys.path.insert(0, os.path.dirname(__file__))

import flaskr

application = flaskr.create_app()

#def application(environ, start_response):
#    start_response('200 OK', [('Content-Type', 'text/plain')])
#    message = 'It works!\n'
#    version = 'Py %s\n' % sys.version.split()[0]
#    response = '\n'.join([message, version])
#    return [response.encode()]
