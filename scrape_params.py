#%% 
#test
import json
import pandas as pd

################# PARAMS
# proxy_list
# https://proxyscrape.com/free-proxy-list
# https://www.sslproxies.org/
# https://geonode.com/free-proxy-list
# https://advanced.name/freeproxy
# https://proxy2.webshare.io/

PROXY_JSON_FILE = 'assets/proxies/free-proxy-list.json'
with open(PROXY_JSON_FILE,'r') as f:
    proxies_list = json.load(f)['proxies']
    
proxies_df = pd.DataFrame.from_records(proxies_list)
#%%
proxy_list = proxies_df[(proxies_df['alive']) & (proxies_df['protocol'] == 'http')]['proxy'].to_list()
proxy_df = proxies_df[(proxies_df['alive']) & (proxies_df['protocol'] == 'http')][['ip','port']]
proxy_manual = [
    'https://221.140.235.237:5002',
    'https://114.129.2.82:8081',
]
#proxy_list=proxy_manual
# proxy_df.sample(1).to_numpy().tolist()[0]
# %%
