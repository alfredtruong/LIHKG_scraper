# simple LIHKG scraper with python


## About

A simple scraper to capture text from Hong Kong forum LIHKG posts, which is a good starting point for who interested in web scraping,
It was developed in Python, by using the library [Selenium]




## Installation

1. Setup [Python](https://www.python.org/) and [GIT](https://git-scm.com/) in runtime environment

2. Install library [selenium] (https://pypi.org/project/selenium/)

3. Clone the repository 
    ```
    git clone https://github.com/papatekken/simple-LIHKG-scraper-with-python LIHKG-scraper
    ```

4. In root directory of 'LIHKG-scraper', run following command to start the application, when the application finished the run, a new text file is created with capture data .

    the program is expecting the post ID as argument

    e.g. post ID = 1996060 

    ```
    python hkg.py 1996060
    ```

## License
[MIT](https://github.com/papatekken/simple-LIHKG-scraper-with-python/blob/master/LICENSE)
