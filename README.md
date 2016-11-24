# Overview
Sqewly (pronounced see-kwuhl-ee) is user-configurable backup utility for MySQL.
The script is intended to give a system administrator flexibility over how the
mysqldump command is executed and what actions are taken based on the result of
the dump operation. It has a limited but suitable feature set, specifically it
implements customizable email reporting, user-definable backup expiration, and
optional gzip/tar compression. It has some basic built-in safety logic (i.e. old
backups will not be rotated unless the most recent backup was successful). The
script abstracts configuration information into a separate config file
containing key value attribute pairs parsed by Python's native ConfigParser, and
implements the std-lib subprocess module to handle potential stderr returned by
spawned threads.

# Installation

Download the utility
    
    git clone git@github.com:dsulli99/sqewly.git

Modify the provided sample.conf.  Here is an example.  This configuration will 
delete existing backups older than 5 days if the backup operation succeds, 
will not report that the backup was successful, and compress it using tar.gz 
compression.

```server_address=localhost
database_name=ucpsom_2017
database_username=backup
database_password=thisIsNotValid.
backup_destination=/group/aaa-asap-mysqlbackups/prod
email_to=invalid-destination@example.com
email_from=do-not-reply@someserver.devopsrockstars.com
smtp_server=smtp.smtpserver.com
max_age=5
report_on_success=0
compress=1
```

Cron it.  Here's an example of doing an hourly backup.

```
[root@someserver cron.hourly]# cat /etc/cron.hourly/run_sqewly_jobs.sh
#!/bin/sh
/opt/local/sqewly/sqewly.py -c /opt/local/sqewly/ucpsom_2017.conf
```
