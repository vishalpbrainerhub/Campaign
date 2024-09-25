from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import Select
import hashlib
import time
import re
import csv
import os
import requests
from datetime import datetime
import json

# Set Chrome options to disable search engine choice screen during automation
options = Options()
options.add_argument("--disable-search-engine-choice-screen")
driver = webdriver.Chrome(options=options)  # Initialize the Chrome WebDriver with the specified options
driver.set_window_size(1200, 800)  # Set the browser window size to 1200x800

# Load configuration settings from the 'config.json' file
def load_config():
    """
    Loads the configuration from 'config.json' file.
    This configuration contains URLs and credentials for the website.
    """
    with open('config.json', 'r') as config_file:
        return json.load(config_file)

config = load_config()  # Load config globally for use in other functions

# Function to open the campaign URL and automate the process of creating campaigns
def open_url(sender_names, selected_template, starting_hour, ending_hour, start_date, end_date, offset):
    """
    Automates the process of opening a campaign URL, filling in necessary details, and creating campaigns.
    Parameters:
    - sender_names: List of selected sender names
    - selected_template: Chosen message template
    - starting_hour, ending_hour: Hours between which the campaign will run
    - start_date, end_date: Date range for the campaign
    - offset: Time delay between processing campaigns in seconds
    """
    url = config['campaign_creation_url']  # Fetch campaign URL from config
    driver.get(url)  # Navigate to the campaign creation URL

    # Wait for the page to load and find the name input field before proceeding
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'name')))

    # Directory containing CSV files with recipients
    directory = 'recipients/split'
    files = [f for f in os.listdir(directory) if f.endswith('.csv')]

    # Helper function to click buttons
    def click_on_button(target_element, xpath):
        """
        Waits for the target button to be clickable and returns it.
        """
        target_button = WebDriverWait(target_element, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        return target_button

    # Iterate over each CSV file and create a campaign
    for index_t, file_name in enumerate(files, start=1):
        
        if index_t > 1:  # If it's not the first campaign, we create a new campaign
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Create new campaign']"))
            )
            button.click()
            time.sleep(1)

            # Click to select SMS Outbound Only campaign type
            outbound_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//p[text()='SMS Outbound Only']/ancestor::button"))
            )
            outbound_button.click()

        time.sleep(1)
        div_elements = driver.find_element(By.CLASS_NAME, 'sc-kqNxZD')  # Find main campaign div container
        child_divs = div_elements.find_elements(By.XPATH, './div')  # Get all child divs within the container

        for index, child_div in enumerate(child_divs):
            # Generate unique name, description, and sender_id for the campaign
            name = file_name[:4] + str(index_t)
            description = file_name[:4] + "_desc" + str(index_t)
            unique_string = f"{file_name[:4]}ID{index_t}{int(time.time())}"
            hash_object = hashlib.md5(unique_string.encode())
            sender_id = hash_object.hexdigest()[:11]

            if index == 1:
                # Fill in campaign name and description in the first section
                input_element_name = child_div.find_element(By.ID, 'name')
                input_element_name.send_keys(f"Test Campaign {name}")
                time.sleep(0.5)

                input_element_description = child_div.find_element(By.ID, 'description')
                input_element_description.send_keys(f"Test Campaign {description}")
                time.sleep(0.5)

                # Tag selection (dropdown)
                input_element_tag = WebDriverWait(child_div, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'search'))
                )
                input_element_tag.click()
                time.sleep(1)
                
                # Wait for and select the "test" tag from dropdown options
                wait = WebDriverWait(driver, 10)
                options = wait.until(EC.visibility_of_all_elements_located((By.XPATH, "//div[@role='listbox']//div[@role='option']")))
                for option in options:
                    if option.text == "test":
                        option.click()
                        break

                time.sleep(1)
                click_on_button(child_div, "//button[contains(text(), 'save & next')]").click()

            elif index == 2:
                # Handle contact list creation in this section
                wait = WebDriverWait(driver, 10)
                button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'sc-gsFSXq') and contains(@class, 'sc-imWYAI')]/span[text()='create new contact list']")))
                button.click()
                time.sleep(1)
                input_element_name = wait.until(EC.presence_of_element_located((By.ID, 'name')))
                input_element_name.send_keys(f"Test Campaign {name}")
                time.sleep(0.5)
                input_element_description = wait.until(EC.presence_of_element_located((By.ID, 'description')))
                input_element_description.send_keys(f"Test Campaign {description}")
                time.sleep(0.5)

                # Upload CSV file for contacts
                file_path = os.path.join(directory, file_name)
                file_path = os.path.abspath(file_path)
                file_input = child_div.find_element(By.XPATH, "//input[@accept='.csv']")
                driver.execute_script("arguments[0].style.display = 'block';", file_input)
                time.sleep(1)
                file_input.send_keys(file_path)
                time.sleep(3)

                # Complete the import and save contact list
                form = child_div.find_element(By.XPATH, "//form[@class='sc-hOynoF hTEFiW']")
                save_next_button = form.find_element(By.XPATH, ".//button[@type='submit']")
                if save_next_button.is_displayed() and save_next_button.is_enabled():
                    save_next_button.click()

                    # After import, select the contact list and continue
                    new_contact_list_div = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'sc-jxOSlx') and contains(@class, 'cviCtm')]"))
                    )
                    click_on_button(child_div, "//div[@role='combobox' and contains(@class, 'ui search top pointing dropdown cp-dropdown selection')]").click()
                    time.sleep(1)
                    dropdown = WebDriverWait(child_div, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="combobox"]'))
                    )
                    phone_option = child_div.find_element(By.XPATH, "//span[contains(@class, 'cp-text') and text()='Phone']")
                    phone_option.click()
                    time.sleep(1)

                    # Finalize the import and proceed
                    click_on_button(child_div, "//button[contains(@class, 'ui primary button') and contains(text(), 'import contacts')]").click()
                    time.sleep(7)
                    click_on_button(child_div, "//button[contains(@class, 'ui primary button') and text()='Continue']").click()
                    time.sleep(1)
                    click_on_button(child_div, "//button[contains(@class,'ui primary right floated button  buttonV2') and text()='save & next']").click()
                    time.sleep(1)
                else:
                    print("Button is not clickable.")

            elif index == 3:
                # Handle the sender name selection in this section
                time.sleep(3)
                click_on_button(child_div, "//div[@role='combobox' and contains(@class, 'ui multiple search top pointing dropdown cp-dropdown selection')]").click()
                time.sleep(0.5)
                options_to_select = sender_names

                # Select each sender name from the dropdown
                for option_text in options_to_select:
                    click_on_button(child_div, f"//div[contains(@class, 'cp-text') and text()='{option_text}']").click()
                    time.sleep(0.5)
                dropdown_icon = driver.find_element(By.XPATH, "//i[@class='dropdown icon cp-semantic-icon']")
                dropdown_icon.click()

                # Proceed to the next section
                click_on_button(child_div, "//button[contains(@class,'ui primary right floated button  buttonV2') and text()='save & next']").click()

            elif index == 4:
                # Handle the message template selection
                click_on_button(child_div, "//div[@role='combobox' and contains(@class, 'ui search top pointing dropdown cp-dropdown selection')]").click()
                time.sleep(0.5)
                option_to_select = str(selected_template)
                click_on_button(child_div, f"//button[span[text()='{option_to_select}']]").click()
                click_on_button(child_div, "//button[contains(@class,'ui primary right floated button  buttonV2') and text()='save & next']").click()
                time.sleep(2)

            elif index == 5:
                # Set up start and end times, and handle date selection
                time.sleep(5)
                dropdowns = child_div.find_elements(By.XPATH, "//div[contains(@role, 'combobox')]")
                time_list = [starting_hour, ending_hour]

                # Iterate through start and end time dropdowns and select the appropriate times
                for index_3, dropdown in enumerate(dropdowns[0:2]):
                    dropdown.click()
                    time.sleep(1)
                    options = dropdown.find_elements(By.CSS_SELECTOR, 'div[role="listbox"] .cp-dropdown-custom-item-classic')
                    target_time = starting_hour if index_3 == 0 else ending_hour

                    for option in options:
                        if option.text == target_time:
                            option.click()
                            break
                    time.sleep(1)

                # Select the date range
                date_divs = child_div.find_elements(By.XPATH, "//div[@class='field']/div[@class='ui icon input']")
                for date_div in date_divs:
                    date_input = date_div.find_element(By.CSS_SELECTOR, 'input[data-testid="datepicker-input"]')
                    date_input.click()
                    time.sleep(1)
                    date_input.clear()

                    # Enter the date into the date picker
                    date_input.send_keys(start_date if date_divs.index(date_div) == 0 else end_date)
                    time.sleep(1)

                # Deselect specific days of the week if needed (example: "Sun")
                days_to_check = ["Sun"]
                checkboxes = child_div.find_elements(By.CSS_SELECTOR, "div.ui.checkbox")

                for checkbox in checkboxes:
                    label = checkbox.find_element(By.TAG_NAME, "label")
                    if label.text in days_to_check:
                        if not checkbox.is_selected():
                            checkbox.click()

                # Select a specific timezone for the campaign
                timezone_option = 'Select timezone'
                timezone_radios = child_div.find_elements(By.NAME, 'timezoneType')
                for radio in timezone_radios:
                    if radio.get_attribute('value') == timezone_option:
                        if not radio.is_selected():
                            radio.click()
                            print(f"Selected timezone: {timezone_option}")

                click_on_button(child_div, "//button[contains(@class,'ui primary right floated button  buttonV2') and text()='save & next']").click()
                time.sleep(2)

            elif index == 6:
                # Final step to start the campaign
                click_on_button(child_div, "//button[contains(@class,'ui primary right floated button  buttonV2') and text()='save & next']").click()
                time.sleep(2)

                start_campaign_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Start campaign')]"))
                )
                start_campaign_button.click()
                time.sleep(5)

                done_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='done']"))
                )
                done_button.click()

        time.sleep(int(offset))  # Delay between campaign creation
        index_t += 1

# Function to log into the website using the credentials from the config file
def login_to_website():
    """
    Automates the login process using the credentials provided in the config.json file.
    """
    driver.get(config['login_url'])  # Navigate to the login page

    # Wait for the login fields to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'email')))
    username = driver.find_element(By.ID, "email")
    password = driver.find_element(By.ID, "password")

    # Input username and password
    driver.implicitly_wait(2)
    username.send_keys(config['email'])
    password.send_keys(config['password'])
    driver.implicitly_wait(2)

    # Submit the login form
    login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    login_button.click()
    driver.implicitly_wait(2)

# Fetches the sender data from the server
def fetch_sender_data():
    """
    Retrieves the list of approved sender IDs from the server by making an authorized GET request.
    Returns a dictionary mapping sender IDs to their names.
    """
    token = driver.execute_script("return window.localStorage.getItem('ACCESS_TOKEN');")
    url = config['sender_url']
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        senders = {item['id']: item['name'] for item in response.json()['items'] if item.get('approved') == 1}
        return senders
    except requests.RequestException as e:
        print(f"Error fetching sender IDs: {e}")
        return {}

# Fetches the message templates from the server
def fetch_message_templates():
    """
    Retrieves the available message templates from the server by making an authorized GET request.
    Returns a dictionary mapping template IDs to their names and variant counts.
    """
    token = driver.execute_script("return window.localStorage.getItem('ACCESS_TOKEN');")
    url = config['message_template_url']
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        templates = {
            item['id']: f"{item['name']} (includes {len(item['variants'])} variants)"
            for item in response.json()['items']
        }
        return templates
    except requests.RequestException as e:
        print(f"Error fetching message templates: {e}")
        return {}


