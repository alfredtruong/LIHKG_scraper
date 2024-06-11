#%%

from typing import List, Dict
import json
import os
import random
import time
import argparse
import queue
import threading

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from fake_useragent import UserAgent

#pip install chromedriver-autoinstaller
import chromedriver_autoinstaller
chromedriver_autoinstaller.install()

parser = argparse.ArgumentParser(description='LIHKG scraper')
parser.add_argument('--name', help='scrape prefix', default='lihkg')
parser.add_argument('--start', help='first thread id', type=int, default=1)
parser.add_argument('--stop', help='last thread id', type=int, default=10)
parser.add_argument('--threads', help='number of threads', type=int, default=1)
parser.add_argument('--ignore_handled', help='skip handled threads', type=bool, default=True)
parser.add_argument('--verbose', help='talk or not', type=bool, default=True)
parser.add_argument('--webdriver_timeout', help='max thread load time', type=int, default=10)
parser.add_argument('--short_wait_min', help='short wait min seconds', type=int, default=5)
parser.add_argument('--short_wait_max', help='short wait max seconds', type=int, default=10)
parser.add_argument('--long_wait_min', help='long wait min seconds', type=int, default=30)
parser.add_argument('--long_wait_max', help='long wait max seconds', type=int, default=60)

args = parser.parse_args()

lock = threading.Lock()


############### chromedriver
'''
# init seleniumwire
from seleniumwire import webdriver  # Import from seleniumwire
import seleniumwire.undetected_chromedriver as uc

def get_browser(proxy_list):
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('start-maximized')

    # user agent
    ua = UserAgent()
    chrome_options.add_argument(f"--user-agent={ua.random}")

    # proxy ip
    sw_options = {
        'proxy': {
            'https': random.choice(proxy_list)
        }
    }

    driver = webdriver.Chrome(
        options=chrome_options,
        seleniumwire_options=sw_options,
    )

    return driver
'''

############### chromedriver
# init selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
def get_browser(proxy_list):
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--log-level=1")

    # user agent
    ua = UserAgent()
    chrome_options.add_argument(f"--user-agent={ua.random}")

    # proxy
    if USE_PROXY_IP:
        chrome_options.add_argument(f'--proxy-server={random.choice(proxy_list)}')

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
            'idx': None, # comment counter within page
            'topic' : topic, # thread topic
            'title' : title, # thread title
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
        #if VERBOSE: print(f'[capture_thread_subpage] {thread_id} {subpage_id}')
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
    thread_id=3
    '''
    ################### ref data
    thread_url = thread_id_to_url(thread_id) # thread_url
    handled_threads = read_json(THREAD_STATUS_JSON) # load previously handled threads
    
    ################### should revisit previously handled threads?
    if skip_partial_thread_successes:
        # dont revisit thread if something previously saved
        if thread_url in handled_threads:
            if VERBOSE: print(f'[capture_thread][{thread_url}] skip, already visited')
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
        if VERBOSE: print(f'[capture_thread][{thread_url}] handled_subpage_ids = {handled_subpage_ids}')

        # capture unhandled pages
        newly_handled_subpage_ids = []
        for subpage_id in range(1,total_subpages+1):
            if subpage_id in handled_subpage_ids:
                # ignore
                if VERBOSE: print('.',end='') # same line
            else:
                # handle
                if VERBOSE: print('x',end='') # same line
                capture_res = capture_thread_subpage(browser, thread_id,subpage_id)
                if capture_res:
                    newly_handled_subpage_ids.append(subpage_id)
        if VERBOSE: print() # new line

        # batch updated newly handled subpages
        handled_threads = handled_subpage_ids + newly_handled_subpage_ids
        update_thread_handled_subpage_ids(thread_url,thread_id,handled_threads)

    except TimeoutException:
        ################### capture_thread failure
        thread_load_failure(thread_url,thread_id)
        return

# Define a thread worker function
def worker(q, proxy_list):
    browser = get_browser(proxy_list)

    while True:
        # get thread_id
        thread_id = q.get()
        if thread_id is None:  # poison pill, exit the thread
            break

        # sleep
        short_wait = random.uniform(SHORT_WAIT_MIN, SHORT_WAIT_MAX)
        long_wait = 0
        time.sleep(short_wait)
        if random.random() < 0.2:
            long_wait = random.uniform(LONG_WAIT_MIN, LONG_WAIT_MAX)
            time.sleep(long_wait)

        if VERBOSE: print(short_wait,long_wait)
        capture_thread(browser,thread_id)

    if browser is not None:
        browser.quit()

#%%
################################# RUN SETTINGS
# ref
from scrape_params import proxy_list

# settings
if True:
    VERBOSE = args.verbose
    WORKERS = args.workers
    THREAD_FROM = args.start
    THREAD_TO = args.finish
    WEBDRIVER_TIMEOUT = args.webdriver_timeout
    SKIP_VISITED_THREADS = args.ignore_handled
    SHORT_WAIT_MIN = args.short_wait_min
    SHORT_WAIT_MAX = args.short_wait_max
    LONG_WAIT_MIN = args.long_wait_min
    LONG_WAIT_MAX = args.long_wait_max
else:
    VERBOSE = True
    WORKERS = 5
    THREAD_FROM = 1
    THREAD_TO = 100
    WEBDRIVER_TIMEOUT = 10
    SKIP_VISITED_THREADS = False
    SHORT_WAIT_MIN, SHORT_WAIT_MAX = 5, 10
    LONG_WAIT_MIN, LONG_WAIT_MAX = 30, 60

if True:
    USE_PROXY_IP = False
    OUTPUT_FILE_PREFIX = f'lihkg_{THREAD_FROM}_{THREAD_TO}'
    THREAD_STATUS_JSON = f'assets/scrapes/{OUTPUT_FILE_PREFIX}_status.json'
    THREAD_COMMENTS_JSONL = f'assets/scrapes/{OUTPUT_FILE_PREFIX}.jsonl'

if False:
    #%%
    ################################# START
    browser = get_browser(proxy_list)

    capture_thread(browser,1,SKIP_VISITED_THREADS)
    capture_thread(browser,2,SKIP_VISITED_THREADS)
    capture_thread(browser,3,SKIP_VISITED_THREADS)
    capture_thread(browser,4,SKIP_VISITED_THREADS)
    #capture_thread(browser,3716261,SKIP_VISITED_THREADS)

    #capture_thread_subpage(browser,3716261,1)
    #%%


    #%%
    capture_thread_subpage(browser,4,1)
    capture_thread(browser,4)


################################# POPULATE QUEUE
# queue to hold threads to be scraped
q = queue.Queue()

# add thread ids to queue
for url in range(THREAD_FROM,THREAD_TO):
    q.put(url)

# poison pills to kill threads
for _ in range(WORKERS):
    q.put(None)

#%%
################################# POPULATE THREADS
# Create a list to hold the threads
lock = threading.Lock()
threads = []

# Create and start the threads
for i in range(WORKERS):
    t = threading.Thread(target=worker, args=(q, proxy_list))
    t.start()
    threads.append(t)

################################# KICK OFF MULTITHREADED RUN
# Wait for all threads to finish
for t in threads:
    t.join()

#%%

# (nlp_env) alfred@net-g14:~/code/OpenRice/openrice_recommendator$ nohup python scrape_threads_mt.py -start 1 -stop 250000 -threads 50 > scrape_threads_mt_1_250000.out 2>&1 &
# (nlp_env) alfred@net-g14:~/code/OpenRice/openrice_recommendator$ less scrape_threads_mt_1_250000.out 


parser.add_argument('--name', help='scrape prefix', default='lihkg')
parser.add_argument('--start', help='first thread id', type=int, default=1)
parser.add_argument('--stop', help='last thread id', type=int, default=10)
parser.add_argument('--threads', help='number of threads', type=int, default=1)
parser.add_argument('--ignore_handled', help='skip handled threads', type=bool, default=True)
parser.add_argument('--verbose', help='talk or not', type=bool, default=True)
parser.add_argument('--webdriver_timeout', help='max thread load time', type=int, default=10)
