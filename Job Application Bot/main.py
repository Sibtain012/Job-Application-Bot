import time, os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException, ElementClickInterceptedException,
    ElementNotInteractableException, StaleElementReferenceException
)

# === CONFIGURATION ===
load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
PHONE = os.getenv("PHONE")
LOGIN_WAIT = 15
SCROLL_WAIT = 2
APPLY_WAIT = 2

# === SETUP DRIVER ===
options = webdriver.ChromeOptions()
options.add_experimental_option("detach", True)
driver = webdriver.Chrome(options=options)

# === STEP 1: OPEN LINKEDIN JOB SEARCH PAGE ===

driver.get("https://www.linkedin.com/jobs/search/?currentJobId=4262153243&distance=25.0&geoId=101022442&keywords=python%20developer&origin=HISTORY")
time.sleep(LOGIN_WAIT)

# === STEP 2: LOGIN TO LINKEDIN ===
sign_in_btn = driver.find_element(By.XPATH, '//*[@id="base-contextual-sign-in-modal"]/div/section/div/div/div/div[2]/button')
sign_in_btn.click()
time.sleep(3)

driver.find_element(By.ID, 'base-sign-in-modal_session_key').send_keys(EMAIL)
driver.find_element(By.ID, 'base-sign-in-modal_session_password').send_keys(PASSWORD)
driver.find_element(By.XPATH, '//*[@id="base-sign-in-modal"]//button[@type="submit"]').click()
time.sleep(LOGIN_WAIT)

# === STEP 3: LOCATE JOB LIST CONTAINER ===
# The line `job_list = driver.find_element(By.XPATH, '//*[@id="main"]/div/div[2]/div[1]/div/ul')` is
# locating the element on the webpage that contains the list of job postings.
# This line of code is using Selenium to locate an element on the webpage that contains a list of job
# postings. The `driver.find_element` method is searching for an HTML element based on the provided
# XPath expression `'//*[@id="main"]/div/div[2]/div[1]/div/ul'`. Once found, this element is stored in
# the variable `job_list` for further processing.
job_list = driver.find_element(By.XPATH, '//*[@id="main"]/div/div[2]/div[1]/div/ul')
jobs = job_list.find_elements(By.TAG_NAME, "li")

print(f"🔍 Found {len(jobs)} jobs.")

applied_count = 0
for job in jobs:
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", job)
        time.sleep(SCROLL_WAIT)

        # Get job-card container and check if "Easy Apply" exists inside
        try:
            easy_apply_marker = job.find_element(By.XPATH, '//*[@id="ember163"]/div/div/div[1]/ul/li[3]/span')
        except NoSuchElementException:
            print("⏩ Skipping: No Easy Apply badge.")
            continue

        # Click the job to load detail panel
        try:
            clickable = job.find_element(By.CLASS_NAME, "job-card-container")
            clickable.click()
        except (ElementClickInterceptedException, ElementNotInteractableException) as e:
            print("⚠️ Could not click job:", e)
            continue

        time.sleep(APPLY_WAIT)

        # Find and click the "Easy Apply" button in the right panel
        try:
            easy_apply_btn = driver.find_element(By.XPATH, '//*[@id="jobs-apply-button-id"]')
            easy_apply_btn.click()
        except NoSuchElementException:
            print("❌ Easy Apply button not found after job click.")
            continue

        time.sleep(2)

        # Check for presence of note or textarea field (multi-step application)
        try:
            driver.find_element(By.TAG_NAME, "textarea")
            print("📝 Found a note field. Skipping job.")
            driver.find_element(By.CLASS_NAME, 'artdeco-modal__dismiss').click()
            time.sleep(1)
            driver.find_element(By.XPATH, '//button[@data-control-name="discard_application_confirm_btn"]').click()
            continue
        except NoSuchElementException:
            pass  # No textarea — proceed

        # Fill phone number field (dynamic ID pattern)
        try:
            phone_input = driver.find_element(By.XPATH, '//*[contains(@id, "phoneNumber-nationalNumber")]')
            phone_input.clear()
            phone_input.send_keys(PHONE)
        except NoSuchElementException:
            print("📵 Phone number field missing — skipping job.")
            driver.find_element(By.CLASS_NAME, 'artdeco-modal__dismiss').click()
            time.sleep(1)
            driver.find_element(By.XPATH, '//button[@data-control-name="discard_application_confirm_btn"]').click()
            continue

        # Submit application
        try:
            submit_button = driver.find_element(By.XPATH, '//button[@aria-label="Submit application"]')
            submit_button.click()
            applied_count += 1
            print(f"✅ Applied to job #{applied_count}")
            time.sleep(2)
        except NoSuchElementException:
            print("❌ Submit button not found.")
            driver.find_element(By.CLASS_NAME, 'artdeco-modal__dismiss').click()
            time.sleep(1)
            driver.find_element(By.XPATH, '//button[@data-control-name="discard_application_confirm_btn"]').click()
            continue

    except StaleElementReferenceException:
        print("🔄 Job element went stale — skipping.")
        continue

print(f"\n🎯 Done! Successfully applied to {applied_count} jobs.")
driver.quit()
