from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
import time
import re
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

meeting_types = ['DI', 'LE', 'LA', 'ST', 'SE', 'AC', 'CL', 'FI', 'FM',
                 'FW', 'IN', 'IT', 'MU', 'OT', 'PB', 'PR', 'RE']


def scrape(driver, class_name):
    status = []
    for name in class_name:
        driver.get("https://act.ucsd.edu/scheduleOfClasses/scheduleOfClassesStudent.htm")
        # click on 'by code(s)'
        elements = driver.find_element_by_link_text('by code(s)')
        elements.click()

        element = driver.find_element_by_id('courses')
        element.send_keys(name)

        element = driver.find_element_by_id('socFacSubmit')
        element.click()

        element = driver.find_elements_by_class_name('sectxt')
        html_doc = ''
        for elem in element:
            html_doc += elem.get_attribute('innerHTML')

        soup = BeautifulSoup(html_doc, 'lxml').text
        arr = soup.split()

        total_arr = []
        curr_arr = []

        for elem in arr:
            if elem.isnumeric() and int(elem) > 10000:
                continue
            if elem in meeting_types:
                if len(curr_arr) != 0:
                    total_arr.append(curr_arr)
                else:
                    pass
                curr_arr = [elem]
            else:
                curr_arr.append(elem)
        total_arr.append(curr_arr)
        df = pd.DataFrame(total_arr)
        df = df.replace('FULL', 0)
        avail_seats = sum(map(lambda x: float(x) if str(x).isnumeric() else 0, np.array(df[9].dropna())))

        if avail_seats > 0:
            print(f'There are {int(avail_seats)} seats left in {name}.')
            status.append('Not Full')
        else:
            print(f'There is no remaining seat left in {name}.')
            status.append('Full')

        element = driver.find_element_by_link_text('Start a new search')
        element.click()

    return status


driver = webdriver.Chrome(ChromeDriverManager().install())
codes = input("Enter class codes, separated by commas, followed by ENTER: ")
codes = codes.split(sep=',')

email = input('Enter email address you would like notifications to be sent to, followed by ENTER: ')
has_email = False
regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
if re.fullmatch(regex, email):
    has_email = True

init_status = scrape(driver, codes)

while True:
    time.sleep(60)
    update_status = scrape(driver, codes)
    if init_status != update_status:
        message = Mail(
            from_email='qhmaservices@gmail.com',
            to_emails=email,
            subject='Changes in Class Watchlist',
            html_content=f'Current status for {codes} is {update_status}')
        try:
            sg = SendGridAPIClient('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')
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            print(e.message)
    init_status = update_status
