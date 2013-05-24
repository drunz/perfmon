import os
import cherrypy
import perfmon.settings as cfg
import perfmon.yapdi as yapdi


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


def init(options, args):
    configfile = options.config_file or os.path.join(cfg.PROJECT_ROOT, 'perfmon.conf')
    cfg.load_config(configfile)    


def main(options, args):
    from perfmon.backend import endpoints
    from perfmon.backend import database as db
    from perfmon.dashboard.views import Dashboard
    
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

    PIDFILE = '/usr/share/perfmon.pid'
    daemon = yapdi.Daemon(pidfile=PIDFILE)

    if 'start' in args:
        postgresdir = os.path.join(cfg.PROJECT_ROOT, 'postgres')
        db.install_postgres_extensions(postgresdir)

        print "Starting ..."
        daemon.daemonize()
        cherrypy.quickstart(root, config=cpconfig)

    elif 'stop' in args:
        print "Stopping ..."
        daemon.kill()

    elif 'restart' in args:
        print "Restarting ..."
        daemon.restart()

    elif 'console' in args:
        cpconfig['global']['tools.staticdir.debug'] = True
        cpconfig['global']['log.screen'] = True
        cherrypy.quickstart(root, config=cpconfig)

    elif 'status' in args:
        if daemon.status():
            print "Perfmon is RUNNING"
        else:
            print "Perfmon is NOT running"


if __name__ == '__main__':
    options, args = command_line_handler()
    init(options, args)
    main(options, args)
