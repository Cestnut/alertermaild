import time
import os
import pwd

errors = {"sudo":dict(), "su":dict(), "login":dict(), "ssh":dict()}

def follow(file):
    file.seek(0, os.SEEK_END)
    while True:
        line = file.readline()        # sleep if file hasn't been updated
        if not line:
            time.sleep(1)
            continue

        yield line

def sudo_handle(content, date):
    user = content[1]
    if user in errors["sudo"]:
        errors["sudo"][user]["number"] += 3
    else:
        errors["sudo"][user] = dict()
        errors["sudo"][user]["number"] = 3
        errors["sudo"][user]["begin_date"] = date

    attempt_number = errors["sudo"][user]["number"]
    
    if attempt_number >= 6:
        begin_date = errors["sudo"][user]["begin_date"]
        print("Consecutive failed sudo attempt for" 
          "user: {} from date: {} to date:{}. Attempt number {}".format(user, begin_date, date, attempt_number))
    
        errors["sudo"].pop(user)


def sudo_clean(content):
    user_uid = int(content[8].split("uid=")[1].strip(")"))
    user = pwd.getpwuid(user_uid).pw_name
    if user in errors["sudo"]:
        errors["sudo"].pop(user)

def su_handle(content, date):
    src_user = content[5]
    dst_user = content[4].strip(")")
    
    if src_user not in errors["su"]:
        errors["su"][src_user] = dict()

    if dst_user in errors["su"][src_user]:
        errors["su"][src_user][dst_user]["number"] += 1
    else:
        errors["su"][src_user][dst_user] = dict()
        errors["su"][src_user][dst_user]["number"] = 1
        errors["su"][src_user][dst_user]["begin_date"] = date

    attempt_number = errors["su"][src_user][dst_user]["number"]
    
    if attempt_number >= 3:
        begin_date = errors["su"][src_user][dst_user]["begin_date"] 
        print("Consecutive failed su attempt for" 
          "user: {} to user: {} from date: {} to date:{}. Attempt number {}".format(src_user, 
                                                dst_user, begin_date, date, attempt_number))
    
        errors["su"][src_user].pop(dst_user)

def su_clean(content):
    src_user_uid = int(content[8].split("uid=")[1].strip(")"))
    dst_user = content[6].split("(uid=")[0]
    src_user = pwd.getpwuid(src_user_uid).pw_name
    if src_user in errors["su"] and dst_user in errors["su"][src_user]:
        errors["su"][src_user].pop(dst_user)

pwd.getpwuid(1000).pw_name
def login_handle(content, date):
    user = content[7].strip(",").strip("'")
    if user in errors["login"]:
        errors["login"][user]["number"] += 1
    else:
        errors["login"][user] = dict()
        errors["login"][user]["number"] = 1
        errors["login"][user]["begin_date"] = date

    attempt_number = errors["login"][user]["number"]
    
    if attempt_number >= 6:
        begin_date = errors["login"][user]["begin_date"]
        print("Consecutive failed login attempt for" 
          "user: {} from date: {} to date:{}. Attempt number {}".format(user, begin_date, date, attempt_number))
    
        errors["login"].pop(user)

def login_clean(content):
    user = content[6].split("(uid=")[0]
    if user in errors["login"]:
        errors["login"].pop(user)

auth_file = open("/var/log/auth.log", "r")
for line in follow(auth_file):
    line = line.split(" ")
    line = [i.strip() for i in line if i != ""]
    date = " ".join(line[0:3])
    content = line[4:]
    if "sudo" in content[0]:
        if "incorrect" in content[4]:
            sudo_handle(content, date)
        elif "opened" in content[3]:
            sudo_clean(content)
    if "su" in content[0]:
        if "FAILED" in content[1]:
            su_handle(content, date)        
        elif "opened" in content[3]:
            su_clean(content)

    if "login" in content[0]:
        if "FAILED" in content[1]:
            login_handle(content, date)
        if "opened" in content[3]:
            login_clean(content)

    print(errors)