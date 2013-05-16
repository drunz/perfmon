import os
import ujson
import cherrypy
import perfmon.settings as cfg
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


def init():
    options, args = command_line_handler()
    configfile = options.config_file or os.path.join(cfg.PROJECT_ROOT, 'perfmon.conf')
    cfg.load_config(configfile)


def main():
    from perfmon.backend import endpoints
    from perfmon.backend import database as db
    from perfmon.dashboard.views import Dashboard

    postgresdir = os.path.join(cfg.PROJECT_ROOT, 'postgres')
    db.install_postgres_extensions(postgresdir)
    
    root = Dashboard()
    root.query = endpoints.Query()
    root.log = endpoints.Logging()

    cpconfig = {
        'global': {
            'tools.staticdir.debug': False,
            'log.screen': False,
            'server.socket_host': str(cfg.get("service", "host")),
            'server.socket_port': cfg.get("service", "port"),
        },
        '/static': {
            'tools.staticdir.root': cfg.STATIC_ROOT,
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

    cherrypy.quickstart(root, config=cpconfig)

    
    # if options.config_file:
    #   print "Using settings: %s" % options.config_file
    #   cherrypy.quickstart(root, config=options.config_file)
    # else:
    #   cherrypy.quickstart(root, config=config)
    
    # server = wsgiserver.CherryPyWSGIServer(('0.0.0.0', 9090), root, config=os.path.join(PROJECT_ROOT, 'settings.conf'))
    # server.start()


if __name__ == '__main__':
    init()
    main()
