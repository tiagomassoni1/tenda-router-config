import re
import sys
import os
import time
import pandas as pd
from bs4 import BeautifulSoup
import lxml.etree as ET
import csv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.ui import Select
from pymongo import MongoClient
from selenium.common.exceptions import TimeoutException, NoSuchElementException

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
        except NoSuchElementException:
            print("Login elements not found.")
            raise

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
        except NoSuchElementException:
            print('Error getting WIFI credentials')

        if not myssid or not mypwd:
            print('SSID or PASS cannot be blank')
            sys.exit(1)

        return myssid, mypwd

    def loadTemplate(self, unit):
        print("Loading template")
        self.driver.get("http://192.168.1.1/saveconf.asp")
        time.sleep(2)

        # Get the path of the file to be loaded
        filename = os.path.join(os.getcwd(), f'TendaV12Guest_Unit{unit}.xml')
        # Directly interact with the file input element
        file_input = self.driver.find_element(By.XPATH, '//input[@type="file"]')
        file_input.send_keys(filename)

        # Take a screenshot to verify the page state before clicking the restore button
        self.driver.save_screenshot('before_restore_button_click.png')

        # Click the restore button after file selection (adjust if needed)
        try:
            # Wait for the restore button to be clickable
            restore_button = WebDriverWait(self.driver, 60).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='Restore']"))
            )
            restore_button.click()
        except TimeoutException:
            print("Restore button not found or clickable within the timeout period.")
            self.driver.save_screenshot('restore_button_not_found.png')  # Take a screenshot to help debug
            raise

        # Optionally take another screenshot after clicking the button
        self.driver.save_screenshot('after_restore_button_click.png')

        # Wait for the next page or element (e.g., username field)
        WebDriverWait(self.driver, 120).until(EC.presence_of_element_located((By.NAME, "username")))

        return True

    def getmac(self):
        print("Getting MAC Address")
        
        # Navigate to the status page and wait for it to load
        self.driver.get("http://192.168.1.1/status.asp")
        time.sleep(5)  # Add a delay to ensure the page has fully loaded
        
        # Take a screenshot for debugging purposes
        self.driver.save_screenshot('status_page.png')
        
        try:
            # Attempt to find the table
            table = WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located((By.XPATH, '(//table)[3]'))).get_attribute("outerHTML")
            df1 = pd.read_html(table)[0]
            mac = df1.loc[3].at[1]
            return mac
        except TimeoutException as e:
            print("Element not found within the given timeout.")
            print(self.driver.page_source)  # Print the page source to help debug
            raise e

# Main code
hotel = "Diamond"
tenda = Tenda(hotel)
filename = "units.csv"

# Load units from CSV file
with open(filename, "r") as file:
    myunits = list(csv.DictReader(file, delimiter=","))

# Set up browser
tenda.setup_method(hotel)
tenda.login("letmein.123")
time.sleep(3)

# Get the current MAC address
mac = tenda.getmac()

# Match the MAC address to the corresponding unit in the CSV and load the template
for unit in myunits:
    if unit['mac'].upper() == mac.upper():
        thisunit = unit['unit']
        print(f"Mac: {unit['mac']} Unit: {unit['unit']}")
        tenda.loadTemplate(thisunit)

# Clean up and close the browser
tenda.teardown_method()
print("Ready")

sys.exit(0)
