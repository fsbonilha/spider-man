from selenium.webdriver import FirefoxOptions
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from datetime import datetime
import os, csv, sys, time, codecs
from  selenium.webdriver.common.desired_capabilities import DesiredCapabilities

# User Variables 
CSV_PATH = os.path.join(sys.path[0], ('data_' + datetime.today().strftime('%Y-%m-%d_T%H-%M') + '.csv'))
PATH_FIREFOX = 'C:/Users/bonilhfe/AppData/Roaming/Mozilla/Firefox/'
PATH_GECKODRIVER = './usr/local/bin/geckodriver'
IMPLICIT_WAIT = 2.0 #seconds - time selenium will wait for EVERY information, until its found
MAPPING_BATCH_SIZE = 20 # This can't be higher than 20
MAIN_BATCH_SIZE = 100

def get_list():
    # Import seller list from csv file 
    l = []
    with open('seller_list.csv', newline='') as f:
        for row in csv.reader(f):
            l.append(row[0])
        return l

def start_driver():
    # Defining Firefox Driver Configs
    # firefox_options = FirefoxOptions()
    # firefox_options.add_argument('--log-level=3')
    # firefox_options.add_argument('--user-data-dir={}'.format(PATH_FIREFOX))
    # firefox_options.add_argument('--width=1600')
    # firefox_options.add_argument('--height=900')    
    
    firefox_capabilities = DesiredCapabilities.FIREFOX
    firefox_capabilities['binary'] = '/usr/bin/firefox'
    firefox_capabilities['marionette'] = True
    driver = webdriver.Firefox(capabilities=firefox_capabilities)

    # Opening Firefox instance
    # ser = Service(PATH_GECKODRIVER)
    # driver = webdriver.Firefox(executable_path=PATH_GECKODRIVER)
    # driver.implicitly_wait(IMPLICIT_WAIT)
    
    driver.get('https://sclens.corp.amazon.com/')
    input('Logged In? Press enter to continue...\r\n')
    return driver

def map_seller(driver, id_list):
    # Give Permission to access sellers in lens
    # Limit of 20 sellers per request, so we will split it in batches of 20
    batches = [id_list[i:i+MAPPING_BATCH_SIZE] for i in range(0,len(id_list),MAPPING_BATCH_SIZE)]
    
    for batch in batches:
        
        driver.get('https://sclens.corp.amazon.com/user2seller')
        
        els = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.NAME, 'Request'))
        )
        els[0].click()
        
        for id in batch:
            driver.find_element('css selector', '.scl-table-filter-bar-container .scl-clickable').click()
            time.sleep(.1)
        
        row = 0
        time.sleep(1)
        for id in batch:
            
            # Using actions to simulate key presses as this form runs with JS 
            css_tag = 'kat-table-cell:nth-child(1) kat-input'
            els = driver.find_elements('css selector', css_tag)
            el = els[row]
            driver.execute_script("arguments[0].scrollIntoView();", el)
            actions = ActionChains(driver)
            actions.click(on_element=el)    
            actions.send_keys(id)
            actions.perform()
            time.sleep(.05)
            
            css_tag = '.scl-self-request-marketplace-column'
            els = driver.find_elements('css selector', css_tag)
            el = els[row]
            actions.click(on_element=el)
            actions.send_keys('BR')
            actions.perform()
            time.sleep(.15)
            
            actions.send_keys(Keys.DOWN)
            actions.send_keys(Keys.RETURN)
            actions.perform()
            
            time.sleep(.1)
            
            row = row + 1
            
        driver.find_element('css selector', '.scl-upload-button').click() # Submit button
        time.sleep(1)
    
    return True

def change_seller(driver, seller_id):    
    driver.get('https://sclens.corp.amazon.com/grant' )
    time.sleep(1)
    
    # Using ActionChains to simulate key presses as this form runs with JS 
    el = driver.find_element('css selector', 'kat-input')
    actions = ActionChains(driver)
    actions.click(on_element=el)    
    actions.send_keys(seller_id)
    actions.perform()
    
    time.sleep(.2)
    tag = '.scl-grant-page-merchant-search-button kat-button'
    driver.find_element('css selector', tag).click()
    time.sleep(.2)
    
    driver.execute_script('''document.querySelector('input[value="A2Q3Y263D00KWC"]').click()''')
    time.sleep(.2)
    driver.execute_script('''document.querySelector('kat-button[label="Access"]').click()''')
    time.sleep(.5)
    
    
    time.sleep(2)
    
    # Closing popup and changing back to original tab
    
    if len(driver.window_handles) <= 1:
        raise Exception('SCLens failed to grant permission')
    
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    
    return
    
# Caution: this functions will get address for current seller, please use change_seller(driver, seller_id)
def get_data(driver, seller_id):
    data = {}
    
    # Business Address
    driver.get('https://www.sellercentral.amazon.dev/sw/AccountInfo/BusinessAddress/step/BusinessAddress')
    tag = '.a-label .ng-binding'
    try: 
        els = driver.find_elements('css selector', tag)
        info=[el.text for el in els]
    except: 
        info = ['']*11
    
    names=['ba_name', 'country', 'zip_code', 'state', 'city', 'ba_line6', 'address_line1', 'address_line2', 'ship_phone', 
           'ba_line10', 'ba_line11']
           
    data = dict(zip(names,info))
    
    # Phone and E-mail - Notifications Page
    driver.get('https://www.sellercentral.amazon.dev/notifications/preferences/contacts')
    tag = '.contact-email'
    try: email=driver.find_elements('css selector', tag)[0].text
    except: email=''
    tag = '.contact-phone'
    try: phone = driver.find_elements('css selector', tag)[0].text
    except: phone = ''
    data['ntf_email'] = email
    data['ntf_phone'] = phone 
    
    # Shipment Address
    driver.get('https://www.sellercentral.amazon.dev/sbr/ref=xx_shipset_dnav_xx#settings')
    tag='#addressWidget td'
    try:
        els = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(('css selector', tag))
        )
        info=[el.text for el in els]
    except:
        info = ['', '', '', '']
    names = ['dship_name', 'dship_placeholder', 'dship_address', 'dship_time_zone']
    new = dict(zip(names,info))
    data.update(new)
    data['merchant_id'] = seller_id
    
    return data

def export_data(data):
    # Take data from one merchant_id and print it to csv 
    columns = ['merchant_id', 'ba_name', 'country', 'zip_code', 'state', 'city', 'ba_line6', 'address_line1', 'address_line2',
                'ship_phone', 'ba_line10', 'ba_line11', 'ntf_email', 'ntf_phone', 'dship_name', 'dship_placeholder', 'dship_address', 'dship_time_zone']
    file_exists = os.path.isfile(CSV_PATH)
    
    with codecs.open(CSV_PATH, 'a', encoding='utf8') as f:
        writer = csv.DictWriter(f, delimiter=',', lineterminator='\n', fieldnames=columns)
        if not file_exists:
            writer.writeheader()  # file doesn't exist yet, write a header
        writer.writerow(data)
    return 

def error_msg(id):
    columns = ['merchant_id', 'ba_name', 'country', 'zip_code', 'state', 'city', 'ba_line6', 'address_line1', 'address_line2',
            'ship_phone', 'ba_line10', 'ba_line11', 'ntf_email', 'ntf_phone', 'dship_name', 'dship_placeholder', 'dship_address', 'dship_time_zone']
    
    info = [id, '!! ERROR SELECTING SP'] + ['']*(len(columns)-2) # Putting error msg into dict and leaving the rest empty
    
    return dict(zip(columns, info))

def map_only():
    driver = start_driver()    
    sp_list = get_list()
    map_seller(driver, sp_list)
    
    driver.close()
    return

def data_only():
    driver = start_driver()    
    sp_list = get_list()
    
    # For each merchant_id in the file provided
    for id in sp_list:
        # Selecting specific seller in Spoofer
        try: 
            change_seller(driver, id)
        except:
            print('! Error selecting seller id', id)
            continue
        data = get_data(driver, id)
        if not data: # If get_data() fails, go to next seller
            export_data(error_msg(id))
            continue
        print(data, '\r\n')
        export_data(data)
    
    driver.close()
    return

def main():
    driver = start_driver()    
    sp_list = get_list()
    
    
    batches = [sp_list[i:i+MAIN_BATCH_SIZE] for i in range(0,len(sp_list),MAIN_BATCH_SIZE)]
    
    for batch in batches:

        map_seller(driver, batch)
         
        # For each merchant_id in the file provided
        for id in batch:
            # Selecting specific seller in Spoofer
            try:
                change_seller(driver, id)
            except:
                print('! Error selecting seller id', id)
                continue
            data = get_data(driver, id)
            if not data: # If get_data() fails, go to next seller
                export_data(error_msg(id))
                continue
            print(data, '\r\n')
            export_data(data)
    driver.close()
    return
    
if __name__ == '__main__': main()
