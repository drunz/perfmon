import os
from setuptools import setup, find_packages


#expects *.html etc
def find_extra_files(dir, patterns,ignore_us):
    data_files = []
    for dirpath, dirnames, filenames in os.walk(dir):
        ignore = False
        splits = dirpath.split(os.sep)
        for x in ignore_us:
            if x in splits:
                ignore = True
                break
            
        if not ignore:
            if filenames:
                for file in filenames:
                    for pattern in patterns:
                        if file.rfind(pattern) > -1:
                            x = os.path.join(dirpath, '*' + pattern)
                            x = x.replace(dir+os.sep,'')
                            try:
                                data_files.index(x)
                            except ValueError, ex:
                                data_files.append(x)
    return data_files


setup(
    name = "perfmon",
    description = "Performance monitoring service for AAM Producer",
    version = "0.5",
    author = 'Arts Alliance Media',
    author_email='development@artsalliancemedia.com',
    url='http://www.artsalliancemedia.com',
    packages = find_packages(''),
    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        'perfmon': find_extra_files('perfmon', ['.hbs','.html', '.js', '.css', '.jpg', '.png', '.gif', '.txt', '.mo', '.ttf', '.woff', '.sql'], [])
    },
    install_requires = ['psycopg2', 'cherrypy==3.2.2'],
    scripts = ['perfmon/perfmond.py'],
)
