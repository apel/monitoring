For Django to work with apache, it is common to have a venv within the app, where django and djangorestframework get installed. Other packages needed for the app to work are installed by Aquilon outside the venv.

## Packages installed by Aquilon outside the venv
Following the config file that Aquilon uses, the following are the packages installed, in this order:
- httpd
- python3-mod_wsgi (for apache to work with django)
- python3-devel
- gcc (needed for dependencies)
- mariadb.


## Packages installed within the venv
Within venv, the following are installed through pip:
- djangorestframework (3.11.2)
- pymysql (needed for mariadb to work)
- pandas (needed by the app)
- django (2.1.*).

Note that when the version of the packages is specified, the app would not work with a different version (due to dependencies conflicts).
Also, as long as mariadb is installed (both client and server), it is not necessary to install mysqlclient (at least when the OS is Scientific Linux).

Is is also important to note that different types of OS require different packages to be installed. 
The above are the packages that allow the app to work on a scientific linux 7 machine. A Centos machine would require slightly different packages.
