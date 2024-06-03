#%%

import sys
import os
import io
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import random

from typing import List, Dict
import json
#pip install chromedriver-autoinstaller
import chromedriver_autoinstaller
chromedriver_autoinstaller.install()

import threading
lock = threading.Lock()

# init chromedriver
def get_browser():
	if TESTING:
		browser = webdriver.Chrome()
		browser.maximize_window()
	else:
		chrome_options = Options()
		chrome_options.add_argument("--headless=new")
		chrome_options.add_argument(f'--proxy-server={random.choice(proxies_list)}')
		chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
		browser = webdriver.Chrome(options=chrome_options)
	return browser

def add_subpage_comments_to_jsonl(url: str, topic: str, title: str, comments: List[str]):
	# generic dico for this 
	base_dico = {
		'url' : url,
		'topic' : topic,
		'title' : title,
	}
	with lock:
		with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
			for comment in comments:
				base_dico['comment'] = comment
				line = json.dumps(base_dico, ensure_ascii=False)
				f.write(line + '\n')

def capture_subpage_success(filepath: str, url: str):
    with lock:
        with open(filepath, 'a') as f:
            f.write(url + '\n')

def remove_url_from_txt_file(filepath: str, url: str):
	# create tmp file
	tmp_filepath = filepath.replace('.txt','_tmp.txt')
	with open(filepath, 'r') as f1:
		with open(tmp_filepath, 'w') as f2:
			for line in f1:
				if line != url:
					f2.write(line + '\n')
	
	# overwrite existing file
	os.rename(tmp_filepath,filepath)

3706516
# capture comments in thread subpage
def capture_subpage(browser: webdriver.Chrome, subpage_url) -> int:
	# load
	try:
		browser.get(subpage_url)
		print('\t',subpage_url)
		element_present = EC.presence_of_element_located((By.CLASS_NAME, '_2cNsJna0_hV8tdMj3X6_gJ'))
		WebDriverWait(browser, TIMEOUT).until(element_present)
		thread_topic = browser.find_element(By.CLASS_NAME,'_3V1lN0nDwZVDoc14rz7D8w').text,
		thread_title = browser.find_element(By.CLASS_NAME,'_2k_IfadJWjcLJlSKkz_R2-').text, # this probably doesnt work
		comments = [x.text for x in browser.find_elements(By.CLASS_NAME,'_36ZEkSvpdj_igmog0nluzh')],
		add_subpage_comments_to_jsonl(subpage_url,thread_topic,thread_title,comments)
		return 1 # success for this subpage
		add_url_to_txt_file(SUBPAGE_SUCCESS,subpage_url)
	except TimeoutException:
		add_url_to_txt_file(SUBPAGE_FAILURE,subpage_url)
		return 0 # failure for this subpage

def load_thread_failure(thread_url: str):
	pass

def capture_thread_success(thread_url: str):
	pass


# capture entire thread
def capture_thread(browser: webdriver.Chrome, thread_id: int) -> int:
	################### main page
	thread_url = f"http://lihkg.com/thread/{thread_id}"
	print(thread_url)
	try:
		browser.get(thread_url)
		element_present = EC.presence_of_element_located((By.CLASS_NAME, '_36ZEkSvpdj_igmog0nluzh'))
		WebDriverWait(browser, TIMEOUT).until(element_present)
	except TimeoutException:
		################### capture_thread failure
		load_thread_failure(thread_url)
		return 0

	################### identify total subpages
	content = browser.find_element(By.CLASS_NAME,'_1H7LRkyaZfWThykmNIYwpH') # get page container
	opt = content.find_elements(By.TAG_NAME,'option') # get page options (figure out how many pages of info)
	pages = len(opt)

	################### subpage
	subpage_successes = 0
	for subpage in range(1, len(opt)+1):
		subpage_url = f"http://lihkg.com/thread/{thread_id}/page/{subpage}"
		subpage_successes += capture_subpage(browser, subpage_url) # count successes

	################### subpage
	if pages == subpage_successes:
		capture_thread_success(thread_url)
		return 1 # total success
	else:
		capture_thread_failure(thread_url)
		return 0 # something failed

#%%

# close chromedriver
if browser is not None:
	browser.quit()

################################# PARAMS
from scrape_params import user_agents,proxies_list

################################# SETTINGS
OUTPUT_FILE = 'asset/scrape/'

RANGE_FROM = 1
RANGE_TO = 10
RANGE_FILENAME_PREFIX = 'lihkg_{RANGE_FROM}_{RANGE_TO}'
THREAD_SUCCESS = 'assets/scrapes/{RANGE_FILENAME_PREFIX}_thread_success.txt'
THREAD_FAILURE = 'assets/scrapes/{RANGE_FILENAME_PREFIX}_thread_failure.txt'
SUBPAGE_SUCCESS = 'assets/scrapes/{RANGE_FILENAME_PREFIX}_subpage_success.txt'
SUBPAGE_FAILURE = 'assets/scrapes/{RANGE_FILENAME_PREFIX}_subpage_failure.txt'
OUTPUT_FILE = 'assets/scrapes/{RANGE_FILENAME_PREFIX}.jsonl'
TESTING = True
TIMEOUT = 10
TEST_MAX_URLS = 150
WORKERS = 50
WAIT_MIN_SHORT, WAIT_MAX_SHORT = 5, 10
WAIT_MIN_LONG, WAIT_MAX_LONG = 60, 120


browser = get_browser()
capture_thread(browser,1)
#%%

if(len(sys.argv)<2):
	print("no post ID found")
	sys.exit()

print("***simple scrape lihkg ***")
capture_thread(sys.argv[1])
print("Finished")

# %%


# capture_thread(1)