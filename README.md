##description

uwsgi_reload.py is a script for the proper graceful reloading of [uWSGI][1]
vassals in a fastrouter based setup. The following guarantees are provided:
- only one instance of the script can run at any given time
- when the script finishes all the vassals were reloaded or the timeout
  specified by "--timeout" was reached
- during the reload at least 1 vassal is operational at any given time (value
  specified by "--minimum-active-vassals")
- the script is as fast as possible by reloading as many vassals in parallel as
  it can

This setup was inspired by the [Subscription system][2] section in "The Art of
Graceful Reloading" from the official uWSGI documentation. It boils down to this:
- an emperor
- a fastrouter
- multiple vassals subscribing to the fastrouter having 1 process each
- a web server using the fastrouter as a backend

In the [examples][3] directory you'll find some configuration file snippets
that show how all this comes together. They come from a Django project but the
general ideas apply to anything that runs on uWSGI. Here are the files and
their meaning:
- [wsgi.py][4] - WSGI application from a Django project. Note how the slow
  startup problem is solved by making a GET request in the file itself. When
  the uWSGI vassal will be ready to receive connections that lazy Django project will
  already be warmed up.
- [uwsgi_vassal.ini][5] - vassal configuration. You need to create
  "/home/some_user/uwsgi" yourself and make symbolic links for each vassal
  that's going to be running in the directory watched by the emperor like this
  (usually one per CPU core - 8 in this example):
```sh
  cd /etc/uwsgi.d
  for N in $(seq -f '%02.f' 1 8); do ln -s /some/project/dir/uwsgi_vassal.ini "uwsgi_vassal_${N}.ini"; done
```
- [uwsgi.conf.d.fragment][6] - a fragment from "/etc/conf.d/uwsgi" on a Gentoo system.
  Those variables translate more or less to this command line:
```sh
  uwsgi --daemonize "${UWSGI_LOG_FILE}" --emperor "${UWSGI_EMPEROR_PATH}" ${UWSGI_EXTRA_OPTIONS}
```
  It's your job to create ${UWSGI_LOG_FILE} and change its ownership before starting the daemon.
- [nginx.conf.fragment][7] - /etc/nginx/nginx.conf fragment showing how to set
  up an upstream pointing to the fastrouter socket and an optional fixed
  fastrouter key that might come useful when testing or serving the same
  application on multiple server names.
- [uwsgi_reload.sh][8] - a simple wrapper around uwsgi_reload.py to showcase
  the command line arguments used in this setup.

In all these example files you'll find placeholders that you need to change:
- some_user
- some_group
- /home/some_user - the directory where a bunch of files and Unix sockets are created by the vassals
- /some/project/dir - Django project directory where wsgi.py can be found.

##usage

```sh
$ ./uwsgi_reload.py --help
usage: uwsgi_reload.py [-h] --emperor-path <dir> --fastrouter-stats-socket
                       <socket> --emperor-stats-socket <socket>
                       [--vassal-config-file-suffix <string>]
                       [--minimum-active-vassals <int>] [--timeout <int>]
                       [--check-interval <float>] [-q]

Graceful reload for uWSGI vassals.

optional arguments:
  -h, --help            show this help message and exit
  --emperor-path <dir>  directory used by the Emperor
  --fastrouter-stats-socket <socket>
                        Fastrouter statistics socket
  --emperor-stats-socket <socket>
                        Emperor statistics socket
  --vassal-config-file-suffix <string>
                        vassal config file suffix (default: .ini)
  --minimum-active-vassals <int>
                        the minimum number of vassals that should be active at
                        any given time during the reload (default: 1)
  --timeout <int>       how long to wait for the reload of a vassal (default:
                        60)
  --check-interval <float>
                        interval between vassal status checks (seconds)
                        (default: 0.1)
  -q, --quiet           supress output (default: False)
```

##requirements

- Python 2
- [uWSGI][1]

##license

Mozilla Public License Version 2.0

##credits

- author: Stefan Talpalaru <stefantalpalaru@yahoo.com>

- homepage: https://github.com/stefantalpalaru/uwsgi_reload


[1]: http://projects.unbit.it/uwsgi/
[2]: http://uwsgi-docs.readthedocs.org/en/latest/articles/TheArtOfGracefulReloading.html#subscription-system
[3]: examples
[4]: examples/wsgi.py
[5]: examples/uwsgi_vassal.ini
[6]: examples/uwsgi.conf.d.fragment
[7]: examples/nginx.conf.fragment
[8]: examples/uwsgi_reload.sh

