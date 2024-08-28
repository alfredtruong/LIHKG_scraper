# simple LIHKG scraper with python
- single (and multithreaded) scraper for LIHKG
- uses `chromedriver` to load thread (subpages)
- uses `BeautifulSoup` to extract relevant items

## Usage
capture a single thread
```python
from scrape_params import proxy_list # load params
browser = get_browser_list(proxy_list) # init chromedriver
capture_thread(browser,1) # capture all subpages of a particular thread
```

capture a range of threads with multithreading (look at `nohup_python_script.*` files)
```bash
python3 scrape_threads_mt.py --start 1 --stop 100 --threads 10 --ignore_handled True
```

old stuff
- code from the forked repo `hkg.py`
- non-multithreaded version `scrape_threads.py`

## About
- built off `https://github.com/papatekken/simple-LIHKG-scraper-with-python` with the following improvements
    - batch runnable
    - restartable

## License
[MIT](https://github.com/alfredtruong/LIHKG_scraper)
