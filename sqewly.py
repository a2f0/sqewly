#!/usr/bin/env python3
import configparser
import sys, getopt
from time import gmtime, strftime
import time
import subprocess
import smtplib
from email.mime.text import MIMEText
import os


def main(argv):
    configfile = ""
    try:
        opts, args = getopt.getopt(argv, "hc:", ["ifile="])
    except getopt.GetoptError:
        print("usage: mysqlbackup.py -c <configfile>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print("usage: mysqlbackup.py -c <configfile>")
        elif opt in ("-c"):
            configfile = arg
    if configfile == "":
        print("usage: mysqlbackup.py -c <configfile>")
        sys.exit(2)

    config = configparser.ConfigParser()
    config.read(configfile)
    global server_address
    server_address = config.get("main", "server_address")
    global database_name
    database_name = config.get("main", "database_name")
    database_username = config.get("main", "database_username")
    database_password = config.get("main", "database_password")
    global backup_destination
    backup_destination = config.get("main", "backup_destination")
    global smtp_server
    smtp_server = config.get("main", "smtp_server")
    global email_to
    email_to = config.get("main", "email_to")
    global email_from
    email_from = config.get("main", "email_from")
    global max_age
    max_age = config.getint("main", "max_age")
    global report_on_success
    report_on_success = config.get("main", "report_on_success")
    global compress
    compress = config.get("main", "compress")

    mysqlfilename = (
        server_address + "-" + strftime("%Y-%m-%d-%H%M", gmtime()) + ".mysql"
    )

    gzipfilename = (
        server_address + "-" + strftime("%Y-%m-%d-%H%M", gmtime()) + ".tar.gz"
    )

    global outputfile
    outputfile = backup_destination + "/" + mysqlfilename

    global gzipoutputfile
    gzipoutputfile = backup_destination + "/" + gzipfilename

    backup_command = (
        "mysqldump --single-transaction -u "
        + database_username
        + " --password="
        + database_password
        + " --databases --host "
        + server_address
        + " "
        + database_name
        + " > "
        + outputfile
    )

    p = subprocess.Popen(
        [
            "mysqldump",
            "--single-transaction",
            "-u",
            database_username,
            "--password=" + database_password,
            "--databases",
            "--host",
            server_address,
            database_name,
        ],
        stdout=open(outputfile, "w"),
        stderr=subprocess.PIPE,
    )
    error = p.stderr.read()

    if (len(error)) > 0:
        action_error(str(error))
        sys.exit(-1)

    if compress == "1":
        p2 = subprocess.Popen(
            [
                "tar",
                "-C",
                backup_destination,
                "--remove-files",
                "--force-local",
                "-czf",
                gzipoutputfile,
                mysqlfilename,
            ],
            stderr=subprocess.PIPE,
        )
        error2 = p2.stderr.read()
        if (len(error2)) > 0:
            action_error(error2)
            sys.exit(-1)

    action_success()


def send_email(subject, body_append):
    body = "Timestamp: " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + "\n"
    body = body + body_append
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = email_from
    msg["To"] = email_to
    s = smtplib.SMTP(smtp_server)
    s.sendmail(email_from, email_to, msg.as_string())


def action_error(error_msg):

    print("An error occurred:\n")
    print(error_msg + "\n")

    subject = (
        "An error occured while backing up " + database_name + " on " + server_address
    )
    body = error_msg
    send_email(subject, body)


def action_success():
    if report_on_success == "1":
        subject = database_name + " was successfully backed up on " + server_address
        if compress:
            final_file = gzipoutputfile
        else:
            final_file = outputfile
        statinfo = os.stat(final_file)
        body = "File path: " + final_file + "\n"
        body = body + "Size: " + sizeof_fmt(statinfo.st_size) + "\n"
        body = body + "Most recent access: " + time.ctime(statinfo.st_atime) + "\n"
        body = (
            body + "Most recent modification: " + time.ctime(statinfo.st_mtime) + "\n"
        )
        send_email(subject, body)
    if max_age > 0:
        now = time.time()
        for f in os.listdir(backup_destination):
            f = os.path.join(backup_destination, f)
            if os.stat(f).st_mtime < now - float(max_age) * 86400:
                if os.path.isfile(f):
                    os.remove(f)


def sizeof_fmt(num):
    for x in ["bytes", "KB", "MB", "GB"]:
        if num < 1024.0 and num > -1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, "TB")


if __name__ == "__main__":
    main(sys.argv[1:])
