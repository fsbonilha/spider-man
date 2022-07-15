from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os, csv, sys, time, codecs

# User Variables 
CSV_PATH = os.path.join(sys.path[0], ('data_' + datetime.today().strftime('%Y-%m-%d_T%H-%M') + '.csv'))
IMPLICIT_WAIT = 1 #seconds 

def get_list():
    # Import seller list from csv file 
    l = []
    with open('seller_list.csv', newline='') as f:
        for row in csv.reader(f):
            l.append(row[0])
        return l

def start_driver():
    # Defining Firefox Driver Configs
    firefox_options = FirefoxOptions()
    firefox_options.add_argument('--log-level=3')
    firefox_options.add_argument('--user-data-dir=C:/Users/bonilhfe/AppData/Roaming/Mozilla/Firefox/')
    firefox_options.add_argument('--width=1600')
    firefox_options.add_argument('--height=900')
    
    
    # Opening Chrome instance
    ser = Service('C:\\geckodriver.exe')
    driver = webdriver.Chrome(options=firefox_options, service = ser)
    driver.implicitly_wait(IMPLICIT_WAIT)
    
    driver.get('https://sclens.corp.amazon.com/')
    input('Logged In? Press enter to continue...')
    return driver
    
def change_seller(driver, seller_id):
    driver.get('https://sellercentral.amazon.com.br/merchant-picker')
    
    # Inputing seller_id provided
    tag = '#spoofed-merchantId-input'
    element = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(('css selector', tag))
    )
    element.clear()
    element.send_keys(seller_id)
    
    # Clicking search
    tag = '.a-button-input'
    driver.find_element('css selector', tag).click()
    # time.sleep(1)
    
    # Trying to find a BR seller in the list
    tag = 'https://sellercentral.amazon.com.br/merchant-picker/change-merchant?marketplaceId=A2Q3Y263D00KWC'
    try: 
        elements = driver.find_elements('xpath', "//a[contains(@href,'"+ tag +"')]")
    except: 
        print('Aviso: Problema ao selecionar o seller', seller_id)
        # append_log(seller_id, 0, '', 'Failed to spoof seller - not found')
        return False
    if len(elements) != 1: # Se mais de um ou nenhum seller encontrado -> ERRO
        print('Aviso: Problema ao selecionar o seller', seller_id)
        # append_log(seller_id, 0, '', f'Failed to spoof seller - found {len(elements)} results')
        return False
    element = elements[0]
    element.click()
    # time.sleep(1)
    return True
    
# Caution: this functions will get address for current seller, please use change_seller(driver, seller_id)
def get_data(driver, seller_id):
    data = {}
    
    # Business Address
    driver.get('https://sellercentral.amazon.com.br/sw/AccountInfo/BusinessAddress/step/BusinessAddress')
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
    driver.get('https://sellercentral.amazon.com.br/notifications/preferences/contacts')
    tag = '.contact-email'
    try: email=driver.find_elements('css selector', tag)[0].text
    except: email=''
    tag = '.contact-phone'
    try: phone = driver.find_elements('css selector', tag)[0].text
    except: phone = ''
    data['ntf_email'] = email
    data['ntf_phone'] = phone 
    
    # Shipment Address
    driver.get('https://sellercentral.amazon.com.br/sbr/ref=xx_shipset_dnav_xx#settings')

    tag='#addressWidget td'
    try:
        els = WebDriverWait(driver, 3).until(
            EC.presence_of_all_elements_located(('css selector', tag))
        )
        info=[el.text for el in els]
    except:
        info = ['', '', '']
    names = ['dship_name', 'dship_address', 'dship_time_zone']
    new = dict(zip(names,info))
    data.update(new)
    data['merchant_id'] = seller_id
    
    return data

def export_data(data):
    # Take data from one merchant_id and print it to csv 
    columns = ['merchant_id', 'ba_name', 'country', 'zip_code', 'state', 'city', 'ba_line6', 'address_line1', 'address_line2',
                'ship_phone', 'ba_line10', 'ba_line11', 'ntf_email', 'ntf_phone', 'dship_name', 'dship_address', 'dship_time_zone']
    file_exists = os.path.isfile(CSV_PATH)
    
    with codecs.open(CSV_PATH, 'a', encoding='utf8') as f:
        writer = csv.DictWriter(f, delimiter=',', lineterminator='\n', fieldnames=columns)
        if not file_exists:
            writer.writeheader()  # file doesn't exist yet, write a header
        writer.writerow(data)
    return 

    

def main():
    driver = start_driver()
    login(driver, EMAIL, PASSWORD)
    
    sp_list = get_list()
    
    # For each merchant_id in the file provided
    for id in sp_list:
        # Selecting specific seller in Spoofer
       if not change_seller(driver, id): continue
       data = get_data(driver, id)
       if not data: continue # If get_data() fails, go to next seller 
       print(data, '\r\n')
       export_data(data)
    return
    
if __name__ == '__main__': main()