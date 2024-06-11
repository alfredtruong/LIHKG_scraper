#%%

import os
import sys
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

############### chromedriver
# init
def get_browser():
    if IS_TESTING:
        browser = webdriver.Chrome()
        browser.maximize_window()
    else:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument(f'--proxy-server={random.choice(proxies_list)}')
        chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
        browser = webdriver.Chrome(options=chrome_options)
    return browser

############### json utils
# read file
def read_json(filepath: str):
    # load
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(e)
        data = {}
    return data

# save file
def write_json(filepath: str, dico: Dict[str,object]):
    # overwrite
    with open(filepath, 'w') as f:
        json.dump(dico, f)

############### thread status file
# log failure to load
def thread_load_failure(thread_url: str, thread_id: int):
    with lock:
        # read dico from file
        thread_status_dico = read_json(THREAD_STATUS_JSON)

        # edit dico
        if thread_url in thread_status_dico:
            # existing entry
            thread_status_dico[thread_url]['attempts'] += 1
        else:
            # new entry
            thread_status_dico[thread_url] = {
                'id': thread_id,
                'attempts': 1,
            }

        # overwrite file
        write_json(THREAD_STATUS_JSON, thread_status_dico)

# log handled subpage ids
def update_thread_handled_subpage_ids(thread_url: str, thread_id: int, handled_threads: List[int]):
    with lock:
        # read dico from file
        thread_status_dico = read_json(THREAD_STATUS_JSON)

        # edit dico
        if thread_url in thread_status_dico:
            # existing entry
            thread_status_dico[thread_url]['attempts'] += 1
            thread_status_dico[thread_url]['handled_subpage_ids'] = handled_threads
        else:
            # new entry
            thread_status_dico[thread_url] = {
                'id': thread_id,
                'attempts': 1,
                'handled_subpage_ids': handled_threads,
            }

        # overwrite file
        write_json(THREAD_STATUS_JSON, thread_status_dico)

############### thread comments file
# add scraped comments
def write_comments_to_jsonl(url: str, topic: str, title: str, comments: List[str]):
    # check if file exists, create directory if it doesn't
    dir_path = os.path.dirname(THREAD_COMMENTS_JSONL)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    with lock:
        # generic dico to reuse for each comment
        generic_dico = {
            'url' : url, # subpage url
            'topic' : topic, # thread topic
            'title' : title, # thread title
            'idx': None, # comment counter within page
            'text' : None, # comment text
        }
        # write line for each comment
        with open(THREAD_COMMENTS_JSONL, 'a', encoding='utf-8') as f:
            for i,comment in enumerate(comments):
                generic_dico['idx'] = i # overwrite comment
                generic_dico['text'] = comment # overwrite comment
                #print(f'[write_comments_to_jsonl] {generic_dico}')
                line = json.dumps(generic_dico, ensure_ascii=False) # build line
                #print(f'[write_comments_to_jsonl] {line}')
                f.write(line + '\n') # write line


'''
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

def capture_thread_success(thread_url: str):
    with lock:
        with open(THREAD_SUCCESS_JSON, 'a') as f:
            f.write(thread_url + '\n')

'''
#3706516

# capture comments in thread subpage
def capture_thread_subpage(
    browser: webdriver.Chrome,
    thread_id: int,
    subpage_id: int,
) -> bool:
    # thread_id,subpage_id=1,1
    try:
        # generate url
        thread_subpage_url = thread_id_and_subpage_id_to_url(thread_id,subpage_id)
        
        # load webpage
        browser.get(thread_subpage_url)
        if IS_TESTING: print(f'[capture_thread_subpage] {thread_id} {subpage_id}')
        element_present = EC.presence_of_element_located((By.CLASS_NAME, '_2cNsJna0_hV8tdMj3X6_gJ'))
        WebDriverWait(browser, WEBDRIVER_TIMEOUT).until(element_present)

        # get topic title
        thread_topic_text = browser.find_element(By.CLASS_NAME,'_3V1lN0nDwZVDoc14rz7D8w').find_element(By.TAG_NAME,'span').text

        # get thread title
        thread_title_text = browser.find_element(By.CLASS_NAME,'CrheYfsiQFY-vLMnO378W').text

        # get comments
        #comments = browser.find_element(By.CLASS_NAME,'eslltWt3HgKnG_miBwvfx').find_elements(By.CLASS_NAME,'_2cNsJna0_hV8tdMj3X6_gJ')
        comments = browser.find_element(By.CLASS_NAME,'eslltWt3HgKnG_miBwvfx').find_elements(By.CLASS_NAME,'GAagiRXJU88Nul1M7Ai0H')
        comments_text = [x.text for x in comments]

        # write to file
        write_comments_to_jsonl(thread_subpage_url,thread_topic_text,thread_title_text,comments_text)
        return True # success
    except TimeoutException:
        return False # failure

# generate thread url
def thread_id_to_url(thread_id: int) -> str:
    return f"http://lihkg.com/thread/{thread_id}"

# generate subpage url
def thread_id_and_subpage_id_to_url(thread_id: int, subpage_id: int) -> str:
    return f"http://lihkg.com/thread/{thread_id}/page/{subpage_id}"

# capture entire thread
def capture_thread(
    browser: webdriver.Chrome,
    thread_id: int,
    skip_partial_thread_successes: bool = False, # should ignore threads with partial successes
) -> int:
    '''
    thread_id=4
    '''
    ################### ref data
    thread_url = thread_id_to_url(thread_id) # thread_url
    handled_threads = read_json(THREAD_STATUS_JSON) # load previously handled threads
    
    ################### should revisit previously handled threads?
    if skip_partial_thread_successes:
        # dont revisit thread if something previously saved
        if thread_url in handled_threads:
            if IS_TESTING: print(f'[capture_thread][{thread_url}] skip, already visited')
            return

    ################### go through uncaptured subpages captured
    try:
        # load main page
        browser.get(thread_url)
        element_present = EC.presence_of_element_located((By.CLASS_NAME, '_36ZEkSvpdj_igmog0nluzh'))
        WebDriverWait(browser, WEBDRIVER_TIMEOUT).until(element_present)

        # identify count of subpages
        content = browser.find_element(By.CLASS_NAME,'_1H7LRkyaZfWThykmNIYwpH') # get page container
        options = content.find_elements(By.TAG_NAME,'option') # get page options (figure out how many pages of info)
        total_subpages = len(options)

        # identify subpages to ignore (there maybe new subpages / new comments)
        #print(handled_threads)
        thread_details = handled_threads.get(thread_url,{})
        #print(thread_details)
        handled_subpage_ids = thread_details.get('handled_subpage_ids',[])
        #print(handled_subpage_ids)
        if IS_TESTING: print(f'[capture_thread][{thread_url}] handled_subpage_ids = {handled_subpage_ids}')

        # capture unhandled pages
        newly_handled_subpage_ids = []
        for subpage_id in range(1,total_subpages+1):
            if subpage_id in handled_subpage_ids:
                # ignore
                if IS_TESTING: print(f'[capture_thread][{thread_url}] ignore')
            else:
                # handle
                if IS_TESTING: print(f'[capture_thread][{thread_url}] handle')
                capture_res = capture_thread_subpage(browser, thread_id,subpage_id)
                if capture_res:
                    newly_handled_subpage_ids.append(subpage_id)
        
        # batch updated newly handled subpages
        handled_threads = handled_subpage_ids + newly_handled_subpage_ids
        update_thread_handled_subpage_ids(thread_url,thread_id,handled_threads)

    except TimeoutException:
        ################### capture_thread failure
        thread_load_failure(thread_url,thread_id)
        return

################################# SCRAPE PARAMS
from scrape_params import user_agents,proxies_list

################################# RUN SETTINGS
IS_TESTING = False
WORKERS = 50
THREAD_FROM = 1
THREAD_TO = 10
OUTPUT_FILE_PREFIX = f'lihkg_{THREAD_FROM}_{THREAD_TO}'
THREAD_STATUS_JSON = f'assets/scrapes/{OUTPUT_FILE_PREFIX}_status.json'
THREAD_COMMENTS_JSONL = f'assets/scrapes/{OUTPUT_FILE_PREFIX}.jsonl'
WEBDRIVER_TIMEOUT = 10
SKIP_VISITED_THREADS = True
WAIT_MIN_SHORT, WAIT_MAX_SHORT = 5, 10
WAIT_MIN_LONG, WAIT_MAX_LONG = 60, 120

#%%
################################# START
browser = get_browser()

#%%
capture_thread(browser,1,SKIP_VISITED_THREADS)
capture_thread(browser,2,SKIP_VISITED_THREADS)
capture_thread(browser,3,SKIP_VISITED_THREADS)
capture_thread(browser,4,SKIP_VISITED_THREADS)
#capture_thread(browser,3716261,SKIP_VISITED_THREADS)

#capture_thread_subpage(browser,3716261,1)
#%%

if browser is not None:
    browser.quit()

#%%

if(len(sys.argv)<2):
    print("no post ID found")
    sys.exit()

print("***simple scrape lihkg ***")
print("Finished")

# %%


# capture_thread(1)


# close chromedriver

#%%
capture_thread_subpage(browser,4,1)
capture_thread(browser,4)

# %%



