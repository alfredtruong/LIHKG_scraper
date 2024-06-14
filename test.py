#%%
from selenium_injector.webdriver import Chrome
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--headless=new")
driver = Chrome(chrome_options)

driver.injector.proxy.set_single(host="example_host.com", port=143, password="password", username="user-1")

driver.get("https://whatismyipaddress.com/")

driver.injector.proxy.clear()
driver.quit()
#%%