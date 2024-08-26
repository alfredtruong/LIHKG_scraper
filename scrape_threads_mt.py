#%%

# export PATH="/home/alfred/nfs/code/chromedriver:$PATH"

# APIs
# https://amp.lihkg.com/thread/3612930/page/28

# multithreading (with request
# https://medium.com/@anonymousmaharaj/proxy-and-mulithreading-for-requests-solving-the-429-too-many-requests-problem-in-python-6f64d8b40424

#%%

# how to install chromedriver on linux
# https://skolo.online/documents/webscrapping/

from typing import List, Dict
import json
import os
import random
import time
import argparse
import queue
import threading

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from fake_useragent import UserAgent

#pip install chromedriver-autoinstaller
#import chromedriver_autoinstaller
#chromedriver_autoinstaller.install()

from bs4 import BeautifulSoup

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
def get_browser(proxy_list: List[str]) -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--log-level=1")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    # user agent
    ua = UserAgent()
    chrome_options.add_argument(f"--user-agent={ua.random}")

    # proxy ip
    if USE_PROXY_IP:
        chrome_options.add_argument(f"--proxy-server={random.choice(proxy_list)}")

    # build and return
    time.sleep(random.uniform(0, 10))
    browser = webdriver.Chrome(options=chrome_options)
    return browser

############### json utils
# read file
def read_json(filepath: str) -> Dict[str,object]:
    # load
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(e)
        data = {}
    return data

# save file
def write_json(filepath: str, dico: Dict[str,object]) -> None:
    # overwrite
    with open(filepath, 'w') as f:
        json.dump(dico, f)

############### thread status file
# log failure to load
def thread_load_failure(thread_url: str, thread_id: int) -> None:
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
def update_thread_handled_subpage_ids(thread_url: str, thread_id: int, handled_threads: List[int]) -> None:
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
def write_comments_to_jsonl(url: str, topic: str, title: str, comments: List[str]) -> None:
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
    '''
    thread_id,subpage_id=1,1
    thread_id,subpage_id=2367593,1
    thread_id,subpage_id=26,28
    '''
    try:
        # generate url
        thread_subpage_url = thread_id_and_subpage_id_to_url(thread_id,subpage_id)
        print(thread_subpage_url)

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
        #comments = browser.find_element(By.CLASS_NAME,'eslltWt3HgKnG_miBwvfx').find_elements(By.CLASS_NAME,'GAagiRXJU88Nul1M7Ai0H')
        #comments = browser.find_element(By.CLASS_NAME,'eslltWt3HgKnG_miBwvfx').find_elements(By.CLASS_NAME,'_2cNsJna0_hV8tdMj3X6_gJ')
        #comments = browser.find_element(By.CLASS_NAME,'eslltWt3HgKnG_miBwvfx').find_elements(By.CLASS_NAME,'GAagiRXJU88Nul1M7Ai0H')
        #[x.text for x in comments]

        #parent_elements = browser.find_elements(By.CSS_SELECTOR, "div._2cNsJna0_hV8tdMj3X6_gJ")

        # Get the page source after it's fully loaded
        page_source = browser.page_source

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(page_source, "html.parser")

        # Find all the parent elements
        parent_elements = soup.find_all("div", class_="_2cNsJna0_hV8tdMj3X6_gJ", attrs={"data-ast-root": "true"})

        # Extract the text from each parent element
        for parent_element in parent_elements:
            # Remove the blockquote elements from the parent element
            for blockquote_element in parent_element.find_all("blockquote", class_="_31B9lsqlMMdzv-FSYUkXeV"):
                blockquote_element.decompose()

        # Get the text of the modified parent element
        res = [parent_element.get_text(strip=True) for parent_element in parent_elements]

        '''
        # Find the parent element
        parent_element = browser.find_element(By.CSS_SELECTOR, "div.GAagiRXJU88Nul1M7Ai0H")
        # for i,x in enumerate(parent_elements): print(i,x.text)


        # Get all the child elements of the parent element, excluding the blockquote elements
        child_elements = [elem for elem in parent_element.find_elements(By.CSS_SELECTOR, "*") if elem.tag_name != "blockquote"]
        [x.text for x in child_elements]

        all_elements = browser.find_elements(By.CSS_SELECTOR, "div.GAagiRXJU88Nul1M7Ai0H")
        #all_elements = browser.find_elements(By.CSS_SELECTOR, "div._2cNsJna0_hV8tdMj3X6_gJ > *")
        [x.text for x in all_elements]
        remaining_elements = [elem for elem in all_elements if elem.get_attribute("class") != "_31B9lsqlMMdzv-FSYUkXeV"]
        #[x.text for x in remaining_elements]
        comments_text = [x.text for x in remaining_elements]


        # Loop through the parent elements and remove the blockquote sub-blocks
        for parent_elem in all_elements:
            blockquotes = parent_elem.find_elements(By.CSS_SELECTOR, "blockquote._31B9lsqlMMdzv-FSYUkXeV")
            for blockquote in blockquotes:
                browser.execute_script("arguments[0].remove();", blockquote)

        # Now you can interact with the modified elements
        for parent_elem in all_elements:
            # Perform actions on the modified elements
            print(parent_elem.text)

        '''
        # write to file
        write_comments_to_jsonl(thread_subpage_url,thread_topic_text,thread_title_text,res)
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
    #print('start')

    ################### should revisit previously handled threads?
    if skip_partial_thread_successes:
        # dont revisit thread if something previously saved
        if thread_url in handled_threads:
            if VERBOSE: print(f'[capture_thread][{thread_url}] skip, already visited')
            return

    ################### sleep
    short_wait = random.uniform(SHORT_WAIT_MIN, SHORT_WAIT_MAX)
    long_wait = 0
    time.sleep(short_wait)
    if random.random() < 0.2:
        long_wait = random.uniform(LONG_WAIT_MIN, LONG_WAIT_MAX)
        time.sleep(long_wait)

    if VERBOSE: print(short_wait,long_wait)

    ################### go through uncaptured subpages captured
    try:
        # load main page
        browser.get(thread_url)
        #print('got')
        element_present = EC.presence_of_element_located((By.CLASS_NAME, '_36ZEkSvpdj_igmog0nluzh'))
        WebDriverWait(browser, WEBDRIVER_TIMEOUT).until(element_present)
        #print('waited')

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
def worker(q: queue, proxy_list) -> None:
    # init browser
    browser = get_browser(proxy_list)

    # loop till poison pill
    while True:
        # get thread_id
        thread_id = q.get()
        if thread_id is None:  # if poison pill, exit thread
            break

        capture_thread(browser,thread_id,SKIP_VISITED_THREADS)

    print('done')
    if browser is not None:
        browser.quit()

################################# RUN SETTINGS
# ref
from scrape_params import proxy_list

#%%
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

#%%

# settings
if True:
    VERBOSE = args.verbose
    WORKERS = args.threads
    THREAD_FROM = args.start
    THREAD_TO = args.stop
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
for url in range(THREAD_FROM,THREAD_TO+1):
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
    t.daemon = True  # Set the thread as a daemon
    t.start()
    threads.append(t)

################################# KICK OFF MULTITHREADED RUN
# Wait for the queue to be empty
while not q.empty():
    time.sleep(1)
#%%

'''
parser.add_argument('--name', help='scrape prefix', default='lihkg')
parser.add_argument('--start', help='first thread id', type=int, default=1)
parser.add_argument('--stop', help='last thread id', type=int, default=10)
parser.add_argument('--threads', help='number of threads', type=int, default=1)
parser.add_argument('--ignore_handled', help='skip handled threads', type=bool, default=True)
parser.add_argument('--verbose', help='talk or not', type=bool, default=True)
parser.add_argument('--webdriver_timeout', help='max thread load time', type=int, default=10)
'''


# (nlp_env) alfred@net-g14:~/code/OpenRice/openrice_recommendator$ nohup python scrape_threads_mt.py --start 1 --stop 250000 --threads 5 --ignore_handled False > scrape_threads_mt_1_250000.out 2>&1 &
# (nlp_env) alfred@net-g14:~/code/OpenRice/openrice_recommendator$ less scrape_threads_mt_1_250000.out 

# nohup python scrape_threads_mt.py --start 1       --stop 250000  --threads 10 --ignore_handled False > scrape_threads_mt_1_250000.out 2>&1
# nohup python scrape_threads_mt.py --start 250000  --stop 500001  --threads 10 --ignore_handled True > scrape_threads_mt_0250000_0500001.out 2>&1 &
# nohup python scrape_threads_mt.py --start 500001  --stop 1000001 --threads 10 --ignore_handled True > scrape_threads_mt_0500001_1000001.out 2>&1 &
# nohup python scrape_threads_mt.py --start 1000001 --stop 1500001 --threads 10 --ignore_handled True > scrape_threads_mt_1000001_1500001.out 2>&1 &
# nohup python scrape_threads_mt.py --start 1500001 --stop 2000001 --threads 10 --ignore_handled True > scrape_threads_mt_1500001_2000001.out 2>&1 &
# nohup python scrape_threads_mt.py --start 2000001 --stop 2500001 --threads 10 --ignore_handled True > scrape_threads_mt_2000001_2500001.out 2>&1 &
# nohup python scrape_threads_mt.py --start 2500001 --stop 3000001 --threads 10 --ignore_handled True > scrape_threads_mt_2500001_3000001.out 2>&1 &
# nohup python scrape_threads_mt.py --start 3000001 --stop 3500001 --threads 10 --ignore_handled True > scrape_threads_mt_3000001_3500001.out 2>&1 &
# nohup python scrape_threads_mt.py --start 3500001 --stop 3720000 --threads 10 --ignore_handled True > scrape_threads_mt_3500001_3720000.out 2>&1 &

#out_lihkg-2750000.csv
#out_lihkg-2800000.csv

# THIS DOESNT WORK COS nohup RUN WITHIN ENVIRONMENT, NEED TO RUN nohup OUTSIDE ENVIRONMENT
# nohup python3 scrape_threads_mt.py --start 2850000 --stop 2900000 --threads 10 --ignore_handled True > scrape_threads_mt_2850000_2900000_g12.out 2>&1 & 
# nohup python3 scrape_threads_mt.py --start 2900000 --stop 2950000 --threads 10 --ignore_handled True > scrape_threads_mt_2900000_2950000_g13.out 2>&1 &
# nohup python3 scrape_threads_mt.py --start 2950000 --stop 3000000 --threads 10 --ignore_handled True > scrape_threads_mt_2950000_3000000_g14.out 2>&1 &
# nohup python3 scrape_threads_mt.py --start 3000000 --stop 3050000 --threads 10 --ignore_handled True > scrape_threads_mt_3000000_3050000_g15.out 2>&1 &
# nohup python3 scrape_threads_mt.py --start 3050000 --stop 3100000 --threads 10 --ignore_handled True > scrape_threads_mt_3050000_3100000_g16.out 2>&1 &
# nohup python3 scrape_threads_mt.py --start 3100000 --stop 3150000 --threads 10 --ignore_handled True > scrape_threads_mt_3100000_3150000_g17.out 2>&1 &
# nohup python3 scrape_threads_mt.py --start 3150000 --stop 3200000 --threads 10 --ignore_handled True > scrape_threads_mt_3150000_3200000.out 2>&1 &
# nohup python3 scrape_threads_mt.py --start 3200000 --stop 3250000 --threads 10 --ignore_handled True > scrape_threads_mt_3200000_3250000.out 2>&1 &
# nohup python3 scrape_threads_mt.py --start 3250000 --stop 3300000 --threads 10 --ignore_handled True > scrape_threads_mt_3250000_3300000.out 2>&1 &
# nohup python3 scrape_threads_mt.py --start 3300000 --stop 3350000 --threads 10 --ignore_handled True > scrape_threads_mt_3300000_3350000.out 2>&1 &
# nohup python3 scrape_threads_mt.py --start 3350000 --stop 3400000 --threads 10 --ignore_handled True > scrape_threads_mt_3350000_3400000.out 2>&1 &
# nohup python3 scrape_threads_mt.py --start 3400000 --stop 3450000 --threads 10 --ignore_handled True > scrape_threads_mt_3400000_3450000.out 2>&1 &
# nohup python3 scrape_threads_mt.py --start 3450000 --stop 3500000 --threads 10 --ignore_handled True > scrape_threads_mt_3450000_3500000.out 2>&1 &
# nohup python3 scrape_threads_mt.py --start 3500000 --stop 3550000 --threads 10 --ignore_handled True > scrape_threads_mt_3500000_3550000.out 2>&1 &
# nohup python3 scrape_threads_mt.py --start 3550000 --stop 3600000 --threads 10 --ignore_handled True > scrape_threads_mt_3550000_3600000.out 2>&1 &
# nohup python3 scrape_threads_mt.py --start 3600000 --stop 3650000 --threads 10 --ignore_handled True > scrape_threads_mt_3600000_3650000.out 2>&1 &
# nohup python3 scrape_threads_mt.py --start 3650000 --stop 3700000 --threads 10 --ignore_handled True > scrape_threads_mt_3650000_3700000.out 2>&1 &
# nohup python3 scrape_threads_mt.py --start 3700000 --stop 3750000 --threads 10 --ignore_handled True > scrape_threads_mt_3700000_3750000.out 2>&1 &
# nohup python3 scrape_threads_mt.py --start 3750000 --stop 3800000 --threads 10 --ignore_handled True > scrape_threads_mt_3750000_3800000.out 2>&1 &
# nohup python3 scrape_threads_mt.py --start 3800000 --stop 3850000 --threads 10 --ignore_handled True > scrape_threads_mt_3800000_3850000.out 2>&1 &
# nohup python3 scrape_threads_mt.py --start 3850000 --stop 3900000 --threads 10 --ignore_handled True > scrape_threads_mt_3850000_3900000.out 2>&1 &