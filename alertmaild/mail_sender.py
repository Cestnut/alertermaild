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
        self.mailing_list = self.config["GENERALE"]["MailingList"].split(":")

        #Legge il dizionario reports dal file reports.json. In caso di errore ne inizializza uno vuoto.
        try:
            with open("reports.json", "r") as reports_file:
                reports = json.load(reports_file)
                assert "su" in reports
                assert "sudo" in reports
                assert "login" in reports
        except Exception as e:
            reports = {"sudo":dict(), "su":dict(), "login":dict(), "time_range":0}
            if isinstance(e, json.JSONDecodeError):
                self.log("Error loading from reports.json, defaulting")
            if isinstance(e, AssertionError):
                self.log("Error reports.json was corrupted")

        self.auth_checker = AuthChecker(reports, self.config)

        #Assegna al segnale SIGTERM, ricevuto quando il servizio viene stoppato o riavviato, il metodo di callback
        signal.signal(signal.SIGTERM, self._handle_sigterm)

    #Apre il file di log in modalità append e aggiunge una nuova riga, includendo data ora ed evento
    def log(self, message):
        now = datetime.now()
        now = now.strftime("%d/%m/%Y %H:%M:%S")

        with open(self.log_path, "a") as log_file:
            log_file.write("{} {}\n".format(now, message))

    def start(self):
        host = self.config["GENERALE"]["SMTPhost"]
        port = int(self.config["GENERALE"]["SMTPport"])
        sender = self.config["GENERALE"]["MailSource"]
        receivers = []
        message = """From: Computer <{}>
Subject: Alert

{}
"""
        try:
            self._start_smtp_server()
            self.log("Daemon started")
            smtpObj = None
            #Questo ciclo serve per evitare che il servizio crashi in caso non dovesse avere immediatamente successo la connessione al server SMTP.
            #Questo errore tipicamente avviene quando il server SMTP è appena stato avviato.
            while True:
                try:
                    smtpObj = smtplib.SMTP(host=host, port=port)
                    break
                except smtplib.SMTPServerDisconnected:
                    pass

            #Per ogni alert non vuoto ricevuto dal generatore alerts(), invia la mail a t utti i destinatari.
            for alert in self.auth_checker.alerts():
                if alert != '':
                    receivers = ",".join(self.mailing_list)

                    msg = message.format(sender, alert)
                    smtpObj.sendmail(sender, receivers, msg)

                    self.log("Sent mail. Content: {}".format(alert))
        except smtplib.SMTPConnectError:
            print("Error connecting")

    #Salva sul file reports.json il dizionario reports in formato JSON e stoppa il server SMTP.
    def stop(self):
        with open("reports.json", "w") as reports_file:
            json.dump(self.auth_checker.reports, reports_file)
        self.log("Daemon stopped")
        self._stop_smtp_server()
        sys.exit(0)        
    
    def _start_smtp_server(self):
        os.system("docker compose down -v")
        os.system("docker compose up -d")

    def _stop_smtp_server(self):
        os.system("docker compose down")

    def _handle_sigterm(self, sig, frame):
        self.stop()




alerter = AlerterMail()
alerter.start()
