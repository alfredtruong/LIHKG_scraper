#%%
import requests
from bs4 import BeautifulSoup  
from fake_useragent import UserAgent
from scrape_params_tmp import proxy_list,proxy_df
import random

ua = UserAgent()

def thread_id_and_subpage_id_to_url(thread_id: int, subpage_id: int) -> str:
    return f"http://lihkg.com/thread/{thread_id}/page/{subpage_id}"

url = thread_id_and_subpage_id_to_url(1,1)
url = 'https://whatismyipaddress.com/'

headers = {'User-Agent': ua.random} # user_agent
proxies = {'http': random.choice(proxy_list)} # proxy_pool

#response = requests.get(url, headers=headers, timeout=10)
response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
soup = BeautifulSoup(response.content, 'html.parser')
print(soup)
# %%

from pprint import pp
