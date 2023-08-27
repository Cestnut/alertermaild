import os
import time
from datetime import datetime, timedelta
import pwd

"""
Questa classe monitora il file auth.log ed effettua dei controlli su ogni riga
per vedere se rispetta le regole del file di configurazione e in caso ritorna una segnalazione
"""

class AuthChecker:
    def __init__(self, reports,config):
        self.auth_file_path = "/var/log/auth.log"
        self.reports = reports
        self.config = config

    def alerts(self):
        auth_file = open("/var/log/auth.log", "r")
        for line in self.follow(auth_file):
            line = line.split(" ")
            line = [i.strip() for i in line if i != ""]
            date = " ".join(line[0:3])
            content = line[4:]
            message = ""
            if self.config["GENERALE"]["FasciaOrariaBool"] and content[0] in ["sudo", "su", "login"]:
                message = self.check_hour_range(content, date)
                yield message
            if "sudo" in content[0]:
                if len(content) > 4 and "incorrect" in content[4]:
                    message = self.sudo_failed(content, date)
                elif len(content) > 3 and "opened" in content[3]:
                    message = self.sudo_clean(content)
            elif "su" in content[0]:
                if len(content) > 1 and  "FAILED" in content[1]:
                    message = self.su_failed(content, date)        
                elif len(content) > 3 and  "opened" in content[3]:
                    message = self.su_clean(content)

            elif "login" in content[0]:
                if len(content) > 1 and "FAILED" in content[1]:
                    message = self.login_failed(content, date)
                if len(content) > 3 and  "opened" in content[3]:
                    message = self.login_clean(content)
            yield message

    def follow(self, file):
        file.seek(0, os.SEEK_END)
        while True:
            line = file.readline()        
            if not line:
                time.sleep(1) #sleep per dare il tempo al file di aggiornarsi
                continue

            yield line

    def check_hour_range(self, content, date):
        datetime_hour = datetime.strptime(date[2], '%H:%M:%S')
        
        begin_hour = self.config["GENERALE"]["FasciaOrariaInizio"]
        begin_hour = datetime.strptime(begin_hour, '%H:%M')
        
        end_hour = self.config["GENERALE"]["FasciaOrariaFine"]
        end_hour = datetime.strptime(end_hour, '%H:%M')
        
        cooldown = timedelta(minutes=int(self.config["GENERALE"]["FasciaOrariaIntervalloMinuti"]))

        alert_bool = False

        if not self.reports["time_range"] or datetime_hour >= self.reports["time_range"] + cooldown:
            if end_hour > begin_hour:
                if datetime_hour > begin_hour and datetime_hour < end_hour:
                    alert_bool = True
            else:
                if datetime_hour > begin_hour or datetime_hour < end_hour:
                    alert_bool = True
            
        if alert_bool:
            message = "{} command executed at {}".format(content[0], date[2])
            self.reports["time_range"] = datetime_hour
        else:
            message = ""
        return message        

    def sudo_failed(self, content, date):
        user = content[1]
        if user in self.reports["sudo"]:
            self.reports["sudo"][user]["number"] += 3
        else:
            self.reports["sudo"][user] = dict()
            self.reports["sudo"][user]["number"] = 3
            self.reports["sudo"][user]["begin_date"] = date

        attempt_number = self.reports["sudo"][user]["number"]
        
        if attempt_number >= int(self.config["sudo"]["TentativiFallitiConsecutiviNumero"]):
            begin_date = self.reports["sudo"][user]["begin_date"]
            self.reports["sudo"].pop(user)
            return "Consecutive failed sudo attempt for user: {} from date: {} to date:{}. Attempt number {}".format(user, begin_date, date, attempt_number)

        else:
            return ""

    def sudo_clean(self, content):
        user_uid = int(content[8].split("uid=")[1].strip(")"))
        user = pwd.getpwuid(user_uid).pw_name
        if user in self.reports["sudo"]:
            self.reports["sudo"].pop(user)
        return ""

    def su_failed(self, content, date):
        src_user = content[5]
        dst_user = content[4].strip(")")
        
        if src_user not in self.reports["su"]:
            self.reports["su"][src_user] = dict()

        if dst_user in self.reports["su"][src_user]:
            self.reports["su"][src_user][dst_user]["number"] += 1
        else:
            self.reports["su"][src_user][dst_user] = dict()
            self.reports["su"][src_user][dst_user]["number"] = 1
            self.reports["su"][src_user][dst_user]["begin_date"] = date

        attempt_number = self.reports["su"][src_user][dst_user]["number"]
        
        if attempt_number >= int(self.config["su"]["TentativiFallitiConsecutiviNumero"]):
            begin_date = self.reports["su"][src_user][dst_user]["begin_date"]
            self.reports["su"][src_user].pop(dst_user)
            return "Consecutive failed su attempt for user: {} to user: {} from date: {} to date:{}. Attempt number {}".format(src_user, dst_user, begin_date, date, attempt_number)
        else:
            return ""        

    def su_clean(self, content):
        src_user_uid = int(content[8].split("uid=")[1].strip(")"))
        dst_user = content[6].split("(uid=")[0]
        src_user = pwd.getpwuid(src_user_uid).pw_name
        if src_user in self.reports["su"] and dst_user in self.reports["su"][src_user]:
            self.reports["su"][src_user].pop(dst_user)
        return ""

    def login_failed(self, content, date):
        user = content[7].strip(",").strip("'")
        if user in self.reports["login"]:
            self.reports["login"][user]["number"] += 1
        else:
            self.reports["login"][user] = dict()
            self.reports["login"][user]["number"] = 1
            self.reports["login"][user]["begin_date"] = date

        attempt_number = self.reports["login"][user]["number"]
        
        if attempt_number >= int(self.config["login"]["TentativiFallitiConsecutiviNumero"]):
            begin_date = self.reports["login"][user]["begin_date"]
            self.reports["login"].pop(user)

            return "Consecutive failed login attempt for user: {} from date: {} to date: {}. Attempt number {}".format(user, begin_date, date, attempt_number)
        else:
            return ""

    def login_clean(self,content):
        user = content[6].split("(uid=")[0]
        if user in self.reports["login"]:
            self.reports["login"].pop(user)
        return ""
