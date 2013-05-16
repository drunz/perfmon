import os
import cherrypy
from perfmon.settings import PROJECT_ROOT, STATIC_ROOT
#from cherrypy import wsgiserver


def command_line_handler():
    from optparse import OptionParser
    usage = "usage: %prog [options] [start|stop]"
    parser = OptionParser(usage=usage)
    parser.add_option('--config',
                      dest='config_file',
                      action='store',
                      default=None,
                      help='Specify alternative config file location')
    (options, args) = parser.parse_args()
    return options, args


def main():
    from perfmon.backend import endpoints
    from perfmon.backend import database as db
    from perfmon.dashboard.views import Dashboard

    options, args = command_line_handler()

    basedir = os.path.join(PROJECT_ROOT, 'postgres')
    db.install_postgres_extensions(basedir)
    
    root = Dashboard()
    root.query = endpoints.Query()
    root.log = endpoints.Logging()

    config = {
        'global': {
            'tools.staticdir.debug': True,
            'log.screen': True,
            'server.socket_host': '0.0.0.0',
            'server.socket_port': 9999,
        },
        '/static': {
            'tools.staticdir.root': STATIC_ROOT,
        },
        '/static/css': {
            'tools.staticdir.on':   True,
            'tools.staticdir.dir': 'css',
        },
        '/static/js': {
            'tools.staticdir.on':   True,
            'tools.staticdir.dir': 'js',
        },
        '/static/data': {
            'tools.staticdir.on':   True,
            'tools.staticdir.dir': 'data',
        },
        '/static/tpl': {
            'tools.staticdir.on':   True,
            'tools.staticdir.dir': 'templates',
        },
        '/static/font': {
            'tools.staticdir.on':   True,
            'tools.staticdir.dir': 'font',
        },
        '/static/img': {
            'tools.staticdir.on':   True,
            'tools.staticdir.dir': 'img',
        },
    }

    cherrypy.quickstart(root, config=config)

    
    # if options.config_file:
    #   print "Using settings: %s" % options.config_file
    #   cherrypy.quickstart(root, config=options.config_file)
    # else:
    #   cherrypy.quickstart(root, config=config)
    
    # server = wsgiserver.CherryPyWSGIServer(('0.0.0.0', 9090), root, config=os.path.join(PROJECT_ROOT, 'settings.conf'))
    # server.start()


if __name__ == '__main__':
    main()
