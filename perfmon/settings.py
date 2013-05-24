import os
import json

PROJECT_ROOT  = os.path.abspath(os.path.dirname(__file__))
STATIC_ROOT   = os.path.join(PROJECT_ROOT, 'static')
TEMPLATE_ROOT = os.path.join(PROJECT_ROOT, 'templates')

DEFAULTS = {
    "database": {
        "engine":   "postgresql",
        "name":     "perfmon",
        "host":     "127.0.0.1",
        "port":      5432,
        "user":     "postgres",
        "password": "postgres"
    },
    "service": {
        "host": "0.0.0.0",
        "port": 9999
    }
}

CONFIG = None


def load_config(filename):
    global CONFIG
    if not CONFIG:
        cfg = json.loads(open(filename).read() or '{}')
        if cfg:
            CONFIG = cfg


def get(section, key=None):
    section = CONFIG.get(section, DEFAULTS.get(section))
    return section.get(key) if key else section