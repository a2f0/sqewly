#!/usr/bin/env python3
import configparser
import sys, getopt
from time import gmtime, strftime
import time
import subprocess
import smtplib
from email.mime.text import MIMEText
import os
import argparse


class Sqewly:
    def __init__(self):
        parser = argparse.ArgumentParser(description="Backup a database.")
        parser.add_argument("-c", required=True, type=str)
        args = parser.parse_args()
        config = configparser.ConfigParser()
        config.read(args.c)
        self.server_address = config.get("main", "server_address")
        self.database_name = config.get("main", "database_name")
        self.database_username = config.get("main", "database_username")
        self.database_password = config.get("main", "database_password")
        self.backup_destination = config.get("main", "backup_destination")
        self.smtp_server = config.get("main", "smtp_server")
        self.email_to = config.get("main", "email_to")
        self.email_from = config.get("main", "email_from")
        self.max_age = config.getint("main", "max_age")
        self.report_on_success = config.get("main", "report_on_success")
        self.compress = config.get("main", "compress")

    def backup(self):
        self.mysqlfilename = (
            self.server_address + "-" + strftime("%Y-%m-%d-%H%M", gmtime()) + ".mysql"
        )

        self.gzipfilename = (
            self.server_address + "-" + strftime("%Y-%m-%d-%H%M", gmtime()) + ".tar.gz"
        )

        self.outputfile = self.backup_destination + "/" + self.mysqlfilename
        self.gzipoutputfile = self.backup_destination + "/" + self.gzipfilename

        backup_command = (
            "mysqldump --single-transaction -u "
            + self.database_username
            + " --password="
            + self.database_password
            + " --databases --host "
            + self.server_address
            + " "
            + self.database_name
            + " > "
            + self.outputfile
        )

        p = subprocess.Popen(
            [
                "mysqldump",
                "--single-transaction",
                "-u",
                self.database_username,
                "--password=" + self.database_password,
                "--databases",
                "--host",
                self.server_address,
                self.database_name,
            ],
            stdout=open(self.outputfile, "w"),
            stderr=subprocess.PIPE,
        )
        error = p.stderr.read()

        if (len(error)) > 0:
            action_error(str(error))
            sys.exit(-1)

        if self.compress == "1":
            p2 = subprocess.Popen(
                [
                    "tar",
                    "-C",
                    self.backup_destination,
                    "--remove-files",
                    "--force-local",
                    "-czf",
                    self.gzipoutputfile,
                    self.mysqlfilename,
                ],
                stderr=subprocess.PIPE,
            )
            error2 = p2.stderr.read()
            if (len(error2)) > 0:
                action_error(error2)
                sys.exit(-1)

        self.action_success()

    def send_email(self, subject, body_append):
        body = "Timestamp: " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + "\n"
        body = body + body_append
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = email_from
        msg["To"] = email_to
        s = smtplib.SMTP(smtp_server)
        s.sendmail(email_from, email_to, msg.as_string())

    def action_error(self, error_msg):
        subject = (
            "An error occured while backing up "
            + self.database_name
            + " on "
            + self.server_address
        )
        body = error_msg
        self.send_email(subject, body)

    def action_success(self):
        if self.report_on_success == "1":
            subject = (
                self.database_name
                + " was successfully backed up on "
                + self.server_address
            )
            if self.compress:
                final_file = self.gzipoutputfile
            else:
                final_file = self.outputfile
            statinfo = os.stat(final_file)
            body = "File path: " + final_file + "\n"
            body = body + "Size: " + sizeof_fmt(statinfo.st_size) + "\n"
            body = body + "Most recent access: " + time.ctime(statinfo.st_atime) + "\n"
            body = (
                body
                + "Most recent modification: "
                + time.ctime(statinfo.st_mtime)
                + "\n"
            )
            send_email(subject, body)
        if self.max_age > 0:
            now = time.time()
            for f in os.listdir(self.backup_destination):
                f = os.path.join(self.backup_destination, f)
                if os.stat(f).st_mtime < now - float(self.max_age) * 86400:
                    if os.path.isfile(f):
                        os.remove(f)

    def sizeof_fmt(num):
        for x in ["bytes", "KB", "MB", "GB"]:
            if num < 1024.0 and num > -1024.0:
                return "%3.1f%s" % (num, x)
            num /= 1024.0
        return "%3.1f%s" % (num, "TB")


sq = Sqewly()
sq.backup()
