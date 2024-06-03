#%%

import sys
import io
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import random

#pip install chromedriver-autoinstaller
import chromedriver_autoinstaller
chromedriver_autoinstaller.install()


def chrome_driver_options():
	my_proxy = random.choice(proxies_list)
	my_user_agent = random.choice(user_agents)
	chrome_options = Options()
	chrome_options.add_argument("--headless=new")
	chrome_options.add_argument(f'--proxy-server={my_proxy}')
	chrome_options.add_argument(f"--user-agent={my_user_agent}")
	return chrome_options

#%%

__version__ = '0.12'

################################# PARAMS
from scrape_params import user_agents,proxies_list
IS_DEV = True

def captureData(thread_id: int):
	browser = webdriver.Chrome(options=chrome_driver_options())
	if IS_DEV:
		browser.maximize_window()

	################### main page
	# load
	page = f"http://lihkg.com/thread/{thread_id}"
	print(page)
	browser.get(page)
	timeout = 10
	try:
		element_present = EC.presence_of_element_located((By.CLASS_NAME, '_36ZEkSvpdj_igmog0nluzh'))
		WebDriverWait(browser, timeout).until(element_present)
	except TimeoutException:
		print ("Timed out waiting for page to load" )
		return None

	# identify total number of subpages for this thread
	content = browser.find_element(By.CLASS_NAME,'_1H7LRkyaZfWThykmNIYwpH') # get page container
	opt = content.find_elements(By.TAG_NAME,'option') # get page options (figure out how many pages of info)
	print(f'opt = {opt}')
	print(f'len(opt) = {len(opt)}')
	
	with io.open(f"{thread_id}Exported.txt", "w", encoding="utf-8") as file:
		################### subpage
		for counter in range(1, len(opt)):
			# load
			subpage = f"http://lihkg.com/thread/{thread_id}/page/{counter}"
			print('\t',subpage)
			browser.get(subpage)
			timeout = 10
			try:
				element_present = EC.presence_of_element_located((By.CLASS_NAME, '_2cNsJna0_hV8tdMj3X6_gJ'))
				WebDriverWait(browser, timeout).until(element_present)
			except TimeoutException:
				file.write(f"Timed out waiting for page {counter} to load")
				return None

		# make sure page loaded
		content = browser.find_elements(By.CLASS_NAME,'_36ZEkSvpdj_igmog0nluzh')
		for x in content:
			file.write("*************************************************")
			file.write(x.text)

	# close output file
	file.close()

	# close chromedriver
	if browser is not None:
		browser.quit()
#%%

if(len(sys.argv)<2):
	print("no post ID found")
	sys.exit()

print("***simple scrape lihkg ***")
print("Version "+__version__)
print(" ")
captureData(sys.argv[1])
print("Finished")

# %%


# captureData(1)