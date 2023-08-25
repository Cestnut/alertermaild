import smtplib
import time
from configparser import ConfigParser
import signal
import os
import sys
import json
from datetime import datetime, timedelta
from time import sleep
from AuthChecker import AuthChecker

class AlerterMail:
    def __init__(self):
        
        self.log_path = "/var/log/alertmaild.log"
        self.config = ConfigParser()
        self.config.read("alertmaild.conf")
        self.mailing_list = self.config["GENERALE"]["MailingList"].split(";")

        #Legge il dizionario reports dal file reports.json. In caso di errore ne crea uno vuoto.
        try:
            with open("reports.json", "r") as reports_file:
                reports = json.load(reports_file)
                assert "su" in reports
                assert "sudo" in reports
                assert "login" in reports
        except Exception as e:
            reports = {"sudo":dict(), "su":dict(), "login":dict(), "ssh":dict(), "time_range":0}
            if isinstance(e, json.JSONDecodeError):
                self.log("Error loading from reports.json, defaulting")
            if isinstance(e, AssertionError):
                self.log("Error reports.json was corrupted")

        self.auth_checker = AuthChecker(reports, self.config)

        signal.signal(signal.SIGTERM, self._handle_sigterm)

    def log(self, message):
        now = datetime.now()
        now = now.strftime("%d/%m/%Y, %H:%M:%S")

        with open(self.log_path, "a") as log_file:
            log_file.write("{} {}\n".format(now, message))

    def follow(file):
        file.seek(0, os.SEEK_END)
        while True:
            line = file.readline()        
            if not line:
                time.sleep(1) #sleep per dare il tempo al file di aggiornarsi
                continue

            yield line  

    def start(self):
        self.log("Daemon started")
        self._start_smtp_server()
        for alert in self.auth_checker.alerts():
            print(alert)

    def stop(self):
        with open("reports.json", "w") as reports_file:
            json.dump(self.auth_checker.reports, reports_file)
        self.log("Daemon stopped")
        self._stop_smtp_server()

    def _start_smtp_server(self):
        os.system("docker compose down -v")
        os.system("docker compose up -d")

    def _stop_smtp_server(self):
        os.system("docker compose down")
        sys.exit(0)

    def _handle_sigterm(self, sig, frame):
        self.stop()


sender = 'from@fromdomain.com'
receivers = ['hihev29182@cwtaa.com']

message = """From: Computer <from@fromdomain.com>
To: To Admin <to@todomain.com>
Subject: Alert

This is a test e-mail message.
"""

"""
try:
    smtpObj = smtplib.SMTP(host='localhost', port=25)
    smtpObj.sendmail(sender, receivers, message)
    print("Mail sent")
except smtplib.SMTPConnectError:
    print("Error connecting")
"""

alerter = AlerterMail()
alerter.start()