Create logs directory
---------------------
**mkdir -p logs**

Create python egg directory
---------------------------
**mkdir -p .python-egg**
chmod -R 777 .python-egg/



Edit httpd.conf
---------------

Add the following line in your httpd.conf (generally present at /etc/apache2/httpd.conf)

Include "/path/to/application/apache/apache_django_wsgi.conf"
