import os
import cherrypy
from perfmon.settings import TEMPLATE_ROOT, STATIC_ROOT


class Dashboard(object):
    """Endpoints for the dashboard (index) view."""
    
    @cherrypy.expose
    def index(self):
        return open(os.path.join(TEMPLATE_ROOT, 'dashboard.html'))
    
    @cherrypy.expose
    def about(self):
        return open(os.path.join(TEMPLATE_ROOT, 'about.html'))
    
    @cherrypy.expose
    def test(self):
        return open(os.path.join(STATIC_ROOT, 'templates', 'base.html'))