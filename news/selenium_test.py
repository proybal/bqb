from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()

driver.get("https://nmpoliticalreport.com/")

title = driver.title

driver.implicitly_wait(0.5)

html = driver.page_source


# element = driver.find_element(By.CLASS_NAME, "gnt_m_he")
# text_box = driver.find_element(by=By.NAME, value="my-text")
# submit_button = driver.find_element(by=By.CSS_SELECTOR, value="button")
#
# text_box.send_keys("Selenium")
# submit_button.click()
#
# message = driver.find_element(by=By.ID, value="message")
# text = message.text

driver.quit()

