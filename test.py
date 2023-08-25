import time
import os
import pwd
from datetime import datetime

reports = {"sudo":dict(), "su":dict(), "login":dict(), "ssh":dict(), "time_range":0}

def follow(file):
    file.seek(0, os.SEEK_END)
    while True:
        line = file.readline()        
        if not line:
            time.sleep(1) #sleep per dare il tempo al file di aggiornarsi
            continue

        yield line

def check_hour_range(date):
    datetime_hour = datetime(date[2], '%H:%M:%S')
    

def sudo_failed(content, date):
    user = content[1]
    if user in reports["sudo"]:
        reports["sudo"][user]["number"] += 3
    else:
        reports["sudo"][user] = dict()
        reports["sudo"][user]["number"] = 3
        reports["sudo"][user]["begin_date"] = date

    attempt_number = reports["sudo"][user]["number"]
    
    if attempt_number >= 6:
        begin_date = reports["sudo"][user]["begin_date"]
        print("Consecutive failed sudo attempt for" 
          "user: {} from date: {} to date:{}. Attempt number {}".format(user, begin_date, date, attempt_number))
    
        reports["sudo"].pop(user)


def sudo_clean(content):
    user_uid = int(content[8].split("uid=")[1].strip(")"))
    user = pwd.getpwuid(user_uid).pw_name
    if user in reports["sudo"]:
        reports["sudo"].pop(user)

def su_failed(content, date):
    src_user = content[5]
    dst_user = content[4].strip(")")
    
    if src_user not in reports["su"]:
        reports["su"][src_user] = dict()

    if dst_user in reports["su"][src_user]:
        reports["su"][src_user][dst_user]["number"] += 1
    else:
        reports["su"][src_user][dst_user] = dict()
        reports["su"][src_user][dst_user]["number"] = 1
        reports["su"][src_user][dst_user]["begin_date"] = date

    attempt_number = reports["su"][src_user][dst_user]["number"]
    
    if attempt_number >= 3:
        begin_date = reports["su"][src_user][dst_user]["begin_date"] 
        print("Consecutive failed su attempt for" 
          "user: {} to user: {} from date: {} to date:{}. Attempt number {}".format(src_user, 
                                                dst_user, begin_date, date, attempt_number))
    
        reports["su"][src_user].pop(dst_user)

def su_clean(content):
    src_user_uid = int(content[8].split("uid=")[1].strip(")"))
    dst_user = content[6].split("(uid=")[0]
    src_user = pwd.getpwuid(src_user_uid).pw_name
    if src_user in reports["su"] and dst_user in reports["su"][src_user]:
        reports["su"][src_user].pop(dst_user)

pwd.getpwuid(1000).pw_name
def login_failed(content, date):
    user = content[7].strip(",").strip("'")
    if user in reports["login"]:
        reports["login"][user]["number"] += 1
    else:
        reports["login"][user] = dict()
        reports["login"][user]["number"] = 1
        reports["login"][user]["begin_date"] = date

    attempt_number = reports["login"][user]["number"]
    
    if attempt_number >= 6:
        begin_date = reports["login"][user]["begin_date"]
        print("Consecutive failed login attempt for" 
          "user: {} from date: {} to date:{}. Attempt number {}".format(user, begin_date, date, attempt_number))
    
        reports["login"].pop(user)

def login_clean(content):
    user = content[6].split("(uid=")[0]
    if user in reports["login"]:
        reports["login"].pop(user)

auth_file = open("/var/log/auth.log", "r")
for line in follow(auth_file):
    line = line.split(" ")
    line = [i.strip() for i in line if i != ""]
    date = " ".join(line[0:3])
    content = line[4:]
    if content[0] in ["sudo", "su", "login"]:
        check_hour_range(date)
    if "sudo" in content[0]:
        if len(content) > 4 and "incorrect" in content[4]:
            sudo_failed(content, date)
        elif len(content) > 3 and "opened" in content[3]:
            sudo_clean(content)
    if "su" in content[0]:
        if len(content) > 1 and  "FAILED" in content[1]:
            su_failed(content, date)        
        elif len(content) > 3 and  "opened" in content[3]:
            su_clean(content)

    if "login" in content[0]:
        if len(content) > 1 and "FAILED" in content[1]:
            login_failed(content, date)
        if len(content) > 3 and  "opened" in content[3]:
            login_clean(content)