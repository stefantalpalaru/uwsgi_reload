#!/bin/sh

./uwsgi_reload.py \
	--emperor-path /etc/uwsgi.d \
	--fastrouter-stats-socket /tmp/uwsgi_fastrouter_stats.sock \
	--emperor-stats-socket /tmp/uwsgi_stats.sock \
	--timeout 30

