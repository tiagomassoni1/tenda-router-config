import re
import sys
import os
import time
import pyautogui
import pandas as pd
from bs4 import BeautifulSoup
import lxml.etree as ET
import csv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import Select
from pymongo import MongoClient

class MongoDB():
    def __init__(self):
        CONNECTION_STRING = "mongodb://10.240.254.227/test"
        self.mongodb = MongoClient(CONNECTION_STRING)
        self.dbname = self.mongodb.get_database()

    def listDevice(self, mac=None):
        collection_name = self.dbname['modems']
        allmodems = collection_name.find({"mac": mac})
        for modem in allmodems:
            return modem

    def updateDevice(self, mac=None, password=None):
        if mac and password:
            modem = self.listDevice(mac.upper())
            if modem:
                print(f"Found {mac.upper()}")
                myquery = {"mac": mac.upper()}
                newvalue = {"$set": {"password": password}}
                collection_name = self.dbname['modems']
                collection_name.update_one(myquery, newvalue)
            else:
                print(f"Not found {mac.upper()} - wifi pass: {password}")
                mydict = {"mac": mac.upper(), "password": password}
                collection_name.insert_one(mydict)
            return True
        else:
            print("Error: couldn't get mac address or password")
            sys.exit(1)

class Tenda():
    def __init__(self, hotel):
        self.hotel = hotel
    
    def setup_method(self, hotel):
        self.op = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(options=self.op)
        self.hotel = hotel

    def teardown_method(self):
        self.driver.close()
        self.driver.quit()

    def login(self, password='admin'):
        print("Initial page")
        self.driver.get("http://192.168.1.1/")
        self.driver.set_window_size(1294, 1386)
        try:
            self.driver.find_element(By.NAME, "username").click()
            self.driver.find_element(By.NAME, "username").send_keys("admin")
            self.driver.find_element(By.NAME, "password").click()
            self.driver.find_element(By.NAME, "password").send_keys(password)
            self.driver.find_element(By.NAME, "save").click()
        except:
            pass

    def firmwareUpgrade(self):
        print("Advanced Options")
        self.driver.get("http://192.168.1.1/upgrade.asp")
        time.sleep(5)
        myelement = self.driver.find_element(By.XPATH, '//*[@id="upgrade_wrap"]/div[1]/div/input').click()
        print(f"Value: {myelement}")

    def getWifi(self):
        self.driver.get("http://192.168.1.1/basicSettings.asp")
        WebDriverWait(self.driver, 120).until(EC.presence_of_element_located((By.ID, "ssid")))
        time.sleep(3)
        try:
            myssid = self.driver.find_element(By.ID, 'ssid').get_attribute('value')
            mypwd = self.driver.find_element(By.ID, 'wrlPwd').get_attribute('value')
        except:
            print('Error getting WIFI credentials')

        if not myssid or not mypwd:
            print('SSID or PASS cannot be blank')
            sys.exit(1)

        return myssid, mypwd

    def configFile(self, wifi):
        modelfile = "Permanent/Model2.xml"
        datafile = "Permanent/MyTenda.xml"
        ssid = wifi['ssid']
        ssid_5g = f"{ssid}_5G"
        password = wifi['password']

        with open(modelfile, 'r', encoding='utf-8') as file:
            data = file.read()

        data = data.replace("%SSIDAUTOMATION%", ssid)
        data = data.replace('%SSIDAUTOMATION_5G%', ssid_5g.strip())
        data = data.replace('%AUTOMATIONPASS%', password.strip())
        data = data.replace('%AUTOMATIONPASS5G%', password.strip())

        with open(datafile, "w") as modem:
            modem.write(data)
        return True

    def permanent(self):
        print("Advanced Options")
        self.driver.get("http://192.168.1.1/saveconf.asp")
        time.sleep(1)

        myelement = self.driver.find_element(By.ID, 'sys_restore')
        myelement.click()
        time.sleep(2)

        filename = os.path.join(os.getcwd(), 'Permanent', 'Permanent-TR069.xml')

        # Open file dialog and type in filename using pyautogui
        time.sleep(1)  # Wait for the file dialog to appear
        pyautogui.write(filename)
        pyautogui.press('enter')  # Press Enter to confirm file selection

        WebDriverWait(self.driver, 120).until(EC.presence_of_element_located((By.NAME, "username")))
        return True

    def dsl_settings(self):
        print("DSL Settings")
        self.driver.get("http://192.168.1.1/admin/adsl-set.asp")
        time.sleep(1)
        myelements = ['glite', 'gdmt', 't1413', 'adsl2', 'adsl2p']
        for thiselement in myelements:
            mycheckbox = self.driver.find_element(By.NAME, thiselement)
            if mycheckbox.is_selected():
                self.driver.execute_script("arguments[0].click();", mycheckbox)
        savebutton = self.driver.find_element(By.NAME, 'save')
        savebutton.click()

    def createTemplate(self, mac, unit):
        srcfilename = "TendaV12Guest_Template.xml"
        dstfilename = f"TendaV12Guest_Unit{unit}.xml"
        wifi_5g = f"U {unit} {self.hotel} 5GHz"
        wifi_24g = f"U {unit} {self.hotel} 2.4GHz"
        search_5g = "%WIFI_NAME%"
        search_24g = "%WIFI_NAME_BACKUP%"

        with open(srcfilename, 'r') as f:
            content = f.read()
            data = content.replace(search_5g, wifi_5g)
            data = data.replace(search_24g, wifi_24g)
            print(data)

        with open(dstfilename, 'w') as d:
            d.write(data)

        return True

# Main code
hotel = "Diamond"
tenda = Tenda(hotel)
time.sleep(3)
filename = "units.csv"
file = open(filename, "r")
myunits = list(csv.DictReader(file, delimiter=","))
file.close()

for unit in myunits:
    tenda.createTemplate(unit['mac'], unit['unit'])

print("Ready")
sys.exit(0)
