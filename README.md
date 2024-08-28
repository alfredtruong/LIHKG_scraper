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

## About
- I build this making use of `https://github.com/papatekken/simple-LIHKG-scraper-with-python`
- improvements made
    - batch runnable
    - can be restarted without redownloading everything

## License
[MIT](https://github.com/alfredtruong/LIHKG_scraper)
