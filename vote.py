import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import random

# =========================
# CONFIGURATION
# =========================


FORM_URL = "http://localhost:8080/vote.php" # replace this with acutal 
CSV_FILE = "C:\\Users\\abc\\users.csv" # replace this with acutal file csv file contain name and email header only

SELECTORS = {
    "radio": (By.ID, "rdo5"),
    "name": (By.ID, "fullname"),
    "email": (By.ID, "email"),
    "captcha_text": (By.XPATH, "//label[@for='captcha_answer']"),
    "captcha_input": (By.ID, "captcha_answer"),
    "submit": (By.XPATH, "//button[contains(text(),'CONFIRM VOTE')]"),
}

HEADLESS = False

# =========================
# CAPTCHA SOLVER
# =========================

def solve_math_captcha(text):
    expression = re.findall(r'[\d\+\-\*/\(\)\s]+', text)
    if not expression:
        return None

    expression = expression[0].strip()

    try:
        result = eval(expression)
        return str(result)
    except:
        return None

# =========================
# HUMAN TYPING Function
# =========================

def human_type(element, text, mistake_chance=0.1):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))

        # Occasionally make a typo
        if random.random() < mistake_chance:
            wrong_char = random.choice("abcdefghijklmnopqrstuvwxyz")
            element.send_keys(wrong_char)
            time.sleep(random.uniform(0.05, 0.12))
            element.send_keys(Keys.BACKSPACE)
            time.sleep(random.uniform(0.05, 0.12))

# =========================
# HUMAN CLICK Function
# =========================

def human_click(driver, element):
    actions = ActionChains(driver)
    actions.move_to_element(element)
    time.sleep(random.uniform(0.3, 0.8))
    actions.click().perform()


# =========================
# DRIVER SETUP
# =========================

def create_driver():
    options = Options()

    if HEADLESS:
        options.add_argument("--headless=new")

    options.add_argument("--start-maximized")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    return driver


# =========================
# MAIN
# =========================

def main():

    data = pd.read_csv(CSV_FILE).dropna()

    driver = create_driver()
    wait = WebDriverWait(driver, 15)

    for index, row in data.iterrows():

        print(f"Processing: {row['email']}")

        # Open new tab
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])

        try:
            driver.get(FORM_URL)
            driver.execute_script("window.scrollBy(0, 250);")
            time.sleep(random.uniform(0.8, 1.5))

	   
            # ===============================
           # RANDOM MULTI SELECTION LOGIC
           # ===============================

           # Get all rdo inputs
            all_options = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[id^='rdo']")))

           # Convert to list
            all_options = list(all_options)

            # Decide whether to include rdo5 (90% chance)
            include_rdo5 = random.random() < 0.9

           # Separate rdo5 and others
            rdo5 = driver.find_element(By.ID, "rdo5")
            other_options = [opt for opt in all_options if opt.get_attribute("id") != "rdo5"]

           # Decide how many total selections (min 1, max 6 or available)
            max_selectable = min(6, len(all_options))

            if include_rdo5:
            # At least 1 (rdo5 already counted)
               total_to_select = random.randint(1, max_selectable)
    
           # Number of extra selections besides rdo5
               extra_count = max(0, total_to_select - 1)
               extra_selected = random.sample(other_options, min(extra_count, len(other_options)))
               final_selection = [rdo5] + extra_selected
            else:
           # Select random options without rdo5
               total_to_select = random.randint(1, min(6, len(other_options)))
               final_selection = random.sample(other_options, total_to_select)

                     # ===============================
                     # CLICK THEM LIKE HUMAN
                     # ===============================

            for option in final_selection:
                 option_id = option.get_attribute("id")

                 label = option.find_element(By.XPATH, "./ancestor::label")

    
                 driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", label)
    
                 time.sleep(random.uniform(0.5, 1.2))
    
                 human_click(driver, label)
    
                 print("Selected IDs:", [opt.get_attribute("id") for opt in final_selection])


            name_field = wait.until(EC.presence_of_element_located(SELECTORS["name"]))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", name_field)
            time.sleep(random.uniform(0.5, 1.0))
            human_type(name_field, row["name"])
           

            email_field = driver.find_element(*SELECTORS["email"])
            human_type(email_field, row["email"])

            time.sleep(random.uniform(0.5, 1.2))

            # Get captcha text
            captcha_element = wait.until(
                EC.presence_of_element_located(SELECTORS["captcha_text"])
            )
            captcha_text = captcha_element.text

            time.sleep(random.uniform(0.5, 1.2))

            captcha_answer = solve_math_captcha(captcha_text)

            if captcha_answer:
                captcha_input = driver.find_element(*SELECTORS["captcha_input"])
                human_type(captcha_input, captcha_answer)
            else:
                print("Captcha could not be solved")
                continue

            time.sleep(1)

            # Submit
            wait.until(EC.element_to_be_clickable(SELECTORS["submit"])).click()


            # Define submit button first
            submit_button = wait.until(EC.element_to_be_clickable(SELECTORS["submit"]))

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});",submit_button)

            time.sleep(random.uniform(0.5, 1.0))

            human_click(driver, submit_button)


            print(f"Submitted: {row['email']}")

        except Exception as e:
            print(f"Error for {row['email']}: {e}")

    print("\nAll users processed. Browser will remain open for verification.")

    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()
