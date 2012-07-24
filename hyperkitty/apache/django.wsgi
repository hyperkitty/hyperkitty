import os
import sys
import site

STAGING=True

if STAGING:
    # staging virtual environment
    vepath = '/home/akhan/.virtualenvs/wackyenv/lib/python2.7/site-packages'
else:
    # live virtual environment
    vepath = '/home/akhan/.virtualenvs/live-server/lib/python2.7/site-packages'

prev_sys_path = list(sys.path)

# add the site-packages of our virtualenv as a site dir
site.addsitedir(vepath)

# add the app's directory to the PYTHONPATH
sys.path.append('/home/akhan/gsoc')

# reorder sys.path so new directories from the addsitedir show up first
new_sys_path = [p for p in sys.path if p not in prev_sys_path]

for item in new_sys_path:
    sys.path.remove(item)
sys.path[:0] = new_sys_path


#Calculate the path based on the location of the WSGI script.
apache_configuration= os.path.dirname(__file__)
project = os.path.dirname(apache_configuration)
workspace = os.path.dirname(project)
sys.path.append(workspace) 


os.environ['DJANGO_SETTINGS_MODULE'] = 'gsoc.apache.settings_production'
# make sure this directory is writable by wsgi process
os.environ['PYTHON_EGG_CACHE'] = '/home/akhan/gsoc/.python-egg'

from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()
