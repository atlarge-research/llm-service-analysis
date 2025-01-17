import time
import os
import traceback
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.support.color import Color


def calculate_start_date(end_date):
    start_date = end_date - relativedelta(months=2)
    start_date_str = start_date.strftime("%Y%m")
    end_date_str = end_date.strftime("%Y%m")
    return start_date_str, end_date_str


def get_archive_path(partition):
    start_date, end_date = calculate_start_date(partition)
    archive_folder = f"data/raw/incident/openai"
    os.makedirs(archive_folder, exist_ok=True)
    return f"{archive_folder}/incident_history_{start_date}_{end_date}.csv"


class MyIncidentPage:
    # Class variable for XPaths that do not change across instances
    UPDATE_XPATH = "//div[@class='row update-row']"
    SERVICE_XPATH = "//div[contains(@class, 'components-affected')]"
    INCIDENT_LIST_XPATH = "//a[contains(@class, 'incident-title')]"
    PAGE_XPATH = "(//h4[contains(@class, 'month-title')])[1]"
    PAGINATION_XPATH = "//div[@class='pagination']//i[@class='left-arrow']"
    SHOW_ALL_XPATH = "//div[contains(@class, 'expand-incidents') and @aria-expanded='false']"

    def __init__(self, driver):
        self.driver = driver
        self.c_key = MAC_C_KEY

    def get_incident_updates(self):
        updates = []
        update_rows = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, self.UPDATE_XPATH))
        )
        # get update by rows
        for update_row in update_rows:
            title = update_row.find_element(By.XPATH, ".//div[contains(@class, 'update-title')]").text
            body = update_row.find_element(By.XPATH, ".//div[contains(@class, 'update-body')]").text
            timestamp = update_row.find_element(By.XPATH, ".//div[contains(@class, 'update-timestamp')]").text

            updates.append({
                    "Update_Title": title,
                    "Update_Body": body,
                    "Update_Timestamp": timestamp
            })

        return json.dumps(updates)

    def get_incident_service(self):
        try:
            service = self.driver.find_element(By.XPATH, self.SERVICE_XPATH).text
        except NoSuchElementException:
            service = None
            print("Service element not found, setting service to None.")
        return service

    def switch_to_incident(self, incident, original_window):
        print("Switch to new window: ")
        title = incident.text
        link = incident.get_attribute('href')
        impact = incident.get_attribute('class').split(' ')[0]
        incident_color = Color.from_string(incident.value_of_css_property('color')).hex
        # switch to new tab to collect incident updates
        incident.send_keys(self.c_key + Keys.RETURN)
        WebDriverWait(self.driver, 10).until(EC.number_of_windows_to_be(2))
        new_window = [window for window in self.driver.window_handles if window != original_window][0]
        self.driver.switch_to.window(new_window)
        # collect incident updates
        # updates = self.get_incident_updates()
        # service = self.get_incident_service()
        record = pd.DataFrame({
            "Incident_Title": [title],
            "Incident_Link": [link],
            "Incident_color": [incident_color],
            "Incident_Impact": [impact],
            "Updates": [self.get_incident_updates()],
            "Service": [self.get_incident_service()]
        })
        # print(record[0]['Incident_Title'], ". ", json.loads(record[0]['Updates'][0])['Update_Timestamp'])
        print(record['Incident_Title'][0], ". ", json.loads(record['Updates'][0])[0]['Update_Timestamp'])
        # switch back
        self.driver.close()
        self.driver.switch_to.window(original_window)
        return record

    def get_incident_list(self):
        try:
            incident_list = WebDriverWait(self.driver, 5).until(
                EC.presence_of_all_elements_located((By.XPATH, self.INCIDENT_LIST_XPATH))
            )
            print("Incidents found in this page: ", len(incident_list))
        except Exception as e:
            print("No incidents found.")
            incident_list = []
        return incident_list

    def archive_incidents(self, incident_df):
        date_str = self.driver.find_element(By.XPATH, self.PAGE_XPATH).text
        date_partition = datetime.strptime(date_str, "%B %Y")
        incident_df.to_csv(get_archive_path(date_partition), index=False)

    def loop_over_incidents(self):
        attempt = 0
        max_attempts = 5
        while attempt < max_attempts:
            incident_df = pd.DataFrame()
            flag_no_data = False
            try:
                # Collecting incident records in new tabs
                incident_list = self.get_incident_list()
                original_window = self.driver.current_window_handle
                if not incident_list:
                    flag_no_data = True
                else:
                    # loop over incidents when there are any
                    for incident_title in incident_list:
                        incident_record = self.switch_to_incident(incident_title, original_window)
                        incident_df = pd.concat([incident_df, pd.DataFrame(incident_record)])
                return incident_df, flag_no_data
            except StaleElementReferenceException:
                print("Stale element, restarting incidents looping process.")
                attempt += 1
                continue
            except Exception as e:
                print("Executing loop_over_incidents(). An error occurred: ", e)
                traceback.print_exc()

        print("\nWarning: this should not happen!!!\n")
        return [], True

    def show_all_incidents(self):
        show_all_buttons = self.driver.find_elements(By.XPATH, self.SHOW_ALL_XPATH)
        if show_all_buttons:
            for show_all in show_all_buttons:
                show_all.click()
            time.sleep(1)

    def go_to_previous_page(self):
        prev_page = self.driver.find_element(By.XPATH, self.PAGINATION_XPATH)
        if prev_page:
            prev_page.click()
            time.sleep(1)

    def collect_data_through_pagination(self):
        """Collect incident reports by incident history pages"""
        try:
            while True:
                # Show all incidents
                self.show_all_incidents()
                # Get incident record by looping over incidents list in the current page
                incident_df, flag_no_data = self.loop_over_incidents()
                # Archive the incidents if there are any
                if len(incident_df) > 0:
                    self.archive_incidents(incident_df)
                # Go to the previous page
                if not flag_no_data:
                    self.go_to_previous_page()
                else:
                    print("No more previous data. Ending incident collecting.")
                    break
        except Exception as e:
            print("Executing collect_data_through_pagination(). An error occurred: ", e)
            traceback.print_exc()



if __name__ == "__main__":

    MAC_C_KEY = Keys.COMMAND
    # WINDOWS_C_KEY = Keys.CONTROL

    driver = webdriver.Chrome()

    driver.get("https://status.openai.com/history/")  # OpenAI incident page
    # driver.get("https://status.anthropic.com/history")  # Anthropic incident page
    # driver.get("https://status.character.ai/history") # CharacterAI incident page


    try:
        incident_page = MyIncidentPage(driver)
        incident_page.collect_data_through_pagination()

    finally:
        # Close the browser
        # input("Press Enter to close the browser")
        driver.quit()
