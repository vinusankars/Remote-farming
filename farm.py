import RPi.GPIO as gp
import time
import smtplib
from urllib2 import urlopen
import re
import io
import csv
import requests
al,mo,wa,f = 0, 0, 0, 0
# ir sensor data-gpio7, power 3V, ground
# soil moisture data-gpio11, power 3V, ground
# transistor for alarm gpio13
# alarm switch gpio16
# motor at gpio21
gp.setwarnings(False)
gp.setmode(gp.BOARD)
def alarm():
    print 'Alarm'
    global al, f
    al = 1
    atime = int(check_values()['Alarm'])
    if f==0:
        email('An animal has creeped into your farm. Do not worry the alarm is on for '+str(atime)+'.')
        f = 1
    gp.setup(13, gp.OUT)
    gp.setup(15, gp.IN)
    logic = True
    start = time.time()
    while logic and time.time()-start <= atime:
        gp.output(13,1)
        check = int(check_values()['Alarm'])
        if gp.input(15)==1:
            logic = False
            al = 0
            gp.output(13,0)
        if check == 0:
            logic = False
            al = 0
    gp.output(13,0)
    gp.output(13,0)
    al = 0
def motion():
    print 'Motion'
    global mo
    mo = 1
    gp.setup(7, gp.IN)
    logic = True
    while logic:
        check = int(check_values()['Motion'])
        if gp.input(7):
            logic = False
        if check == 0:
            logic = False
        elif check == 1:
            logic = True
        else:
            pass
        if gp.input(7) == 1:
            mo = 0
            alarm()
def getTemp():
    print 'Temp'
    data = urlopen('https://weather.com/en-IN/weather/today/l/23.22,72.70?temp=c&par=google').read()
    temp = int(re.findall(r'<div class="today_nowcard-temp"><span class="">(.*?)<sup>',str(data),re.DOTALL)[0])
    return temp
def email(msg):
    print 'Email'
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('**********@gmail.com', 'RPIBTECH2016')
    msg = """Subject: RPi Alert """+msg
    server.sendmail('**********@gmail.com', '*********@iitgn.ac.in', msg)
    server.quit()
def check_moisture():
    global wa
    print 'Check moisture'
    wa = 1
    wtime = int(check_values()['Water'])
    gp.setup(11,gp.IN)
    if gp.input(11)==0:
        email('Soil Moisture Content is above required level.')
    else:
        email('Soil Moisture Content is below required level. Watering will be done for '+str(wtime)+' seconds')
        gp.setup(29,gp.OUT)
        gp.output(29,1)
        time.sleep(wtime)
        gp.output(29,0)
        wa = 0
def check_values():
    headers={}
    headers["User-Agent"]= "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:22.0) Gecko/20100101 Fireox/22.0"
    headers["DNT"]= "1"
    headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    headers["Accept-Encoding"] = "deflate"
    headers["Accept-Language"]= "en-US,en;q=0.5"
    lines = []
    file_id="1AWWqEwiMfl9xL3hdtNeqJLzLBSdlblH-oABTC3uc5RU"
    url = "https://docs.google.com/spreadsheets/d/{0}/export?format=csv".format(file_id)
    req = requests.get(url)
    data = {}
    columns = [] #represents columns of matrix
    let = io.StringIO( req.text, newline=None)
    der = csv.der(let, dialect=csv.excel)
    valuerow = 0
    for row in der:
        if valuerow == 0:
            for column in row:
                data[column] = ''
                columns.append(column)
        else:
            i = 0
            for column in row:
                data[columns[i]] = column
                i += 1
        valuerow += 1
    return data
def reset():
    print 'Reset'
    f, al, mo, wa = 0, 0, 0, 0
def main():
    start = time.time()
    try:
        while True:
            check = check_values()
            if check['Motion'] == '1':
                motion()
            if check['Alarm'] != '0':
                alarm()
            if check['Email'] == '1':
                msg = 'The temperature is '+str(getTemp())+' Alarm is '+str(al)+'.Motor is '+str(wa)+'.Motion IR is '+str(mo)+'.System is working fine.'
                email(msg)
            if check['Water'] != '0':
                check_moisture()
            if check['Reset'] == '1':
                reset()
            if time.time()-start>=7200:
                global f
                reset()
                start = time.time()
    except:
        gp.cleanup()
main()
