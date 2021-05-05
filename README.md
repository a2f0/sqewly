# Overview

Sqewly is a user-configurable backup utility for MySQL that gives a system administrator flexibility over how the `mysqldump` command is executed and what actions are taken based on the result of the dump operation. It has a limited but suitable feature set, specifically:

- customizable email reporting
- user-definable backup expiration
- optional gzip/tar compression

## Development

Run the script against a test container

    docker-compose up --exit-code-from sqewly

## Installation

Cron - Hourly backups

    [root@example cron.hourly]# cat /etc/cron.hourly/run_sqewly_jobs.sh
    #!/bin/sh
    /opt/local/sqewly/sqewly.py -c /opt/local/sqewly/ucpsom_2017.conf
