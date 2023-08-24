import smtplib
from configparser import ConfigParser
import signal
import os
import sys
from time import sleep

class AlerterMail:
    def __init__(self):
        
        config = ConfigParser()
        config.read("alertmaild.conf")
        self.config = config["CONFIGURAZIONE"]

        signal.signal(signal.SIGTERM, self._handle_sigterm)

    def start(self):
        self._start_smtp_server()
        i = 0
        while True:
            with open("newFile.txt", "a") as newfile:
                newfile.write("ciao {}\n".format(i))
                i+=1
            sleep(1)

    def stop(self):
        self._stop_smtp_server()

    def _start_smtp_server(self):
        os.system("docker compose down")
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