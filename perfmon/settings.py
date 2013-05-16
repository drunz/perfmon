import os

PROJECT_ROOT  = os.path.abspath(os.path.dirname(__file__))
STATIC_ROOT   = os.path.join(PROJECT_ROOT, 'static')
TEMPLATE_ROOT = os.path.join(PROJECT_ROOT, 'templates')

DBCONF = {
  "host": "localhost",
  "port": "",
  "name": "perfmon",
  "user": "postgres",
  "password": "postgres",
}
