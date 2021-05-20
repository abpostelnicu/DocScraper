import argparse
import logging
import os
from urllib.parse import urlparse

import wget
import yaml
from selenium import webdriver

already_visited = dict()

def download(link, definition):
    # extract the filename
    filename = os.path.basename(urlparse(link).path)

    # Create path
    path = os.path.join(os.path.abspath(os.getcwd()), "documents", definition["path"])

    # Create dirs
    os.makedirs(path, exist_ok=True)

    wget.download(link, os.path.join(path, filename))


def has_document(link, definition):

    for doc in definition["documents"]:
        if link.lower().endswith(doc.lower()):
            return True


def process_site(site_name, url, definition, driver):
    try:
        driver.get(url)
    except Exception as _:
        logging.error("Exception for {}".format(url))
        return

    elems = driver.find_elements_by_xpath("//a[@href]")

    links = list()

    # Cache hrefs since dom is going to be modified once we do driver.geturl(...)
    for elem in elems:
        retries = 4
        href = None
        while retries > 0:
            try:
                href = elem.get_attribute("href")
                break
            except Exception as _:
                pass

        if href is None:
            i = 0
            i = i + 1
        if href is not None and len(href) > 0:
            links.append(elem.get_attribute("href"))

    for href in links:
        # Did we analyze this?
        if already_visited.get(href, None) is not None:
            # yes we did
            continue
        already_visited[href] = True

        logging.info("Analyze for: {}".format(href))

        if has_document(href, definition):
            logging.info("Found document: {}".format(href))
            download(href, definition)
        else:
            # Do not cross-site
            # This is sub-optimal, should be redone
            if site_name not in href:
                logging.info("Skip {}".format(href))
                continue
            process_site(site_name, href, definition, driver)


def get_driver_options(driver_options):
    driver_options.headless = True

    return driver_options


def process(yml):
    sites = yml.get("sites", None)
    if sites is None:
        exit(1)

    # Try different drivers, the order is:
    # 1. Chrome
    # 2. Firefox - this has some issues when DOM has some unbounded elements, see https://bugzilla.mozilla.org/show_bug.cgi?id=818823
    try:
        from selenium.webdriver.chrome.options import Options

        driver_options = Options()
        # Start selenium driver
        driver = webdriver.Chrome(options=get_driver_options(driver_options))
    except Exception as _:
        try:
            from selenium.webdriver.firefox.options import Options

            driver_options = Options()
            driver_options = get_driver_options(driver_options)

            # Start selenium driver
            driver = webdriver.Firefox(options=driver_options)

        except Exception as _:
            logging.error("Unable to init web driver, tried Firefox and Chrome.")
            exit(1)

    for site in sites:
        for site_name in site:
            process_site(
                site[site_name]["limiter"],
                site[site_name]["url"],
                site[site_name],
                driver,
            )


def main():
    parser = argparse.ArgumentParser(description="Document Scraper from Web")
    parser.add_argument("path", help="File path using YML format for links specifier.")
    args = parser.parse_args()

    # Maybe we can do this to be set dynamic, from the cli
    logging.basicConfig(level=logging.INFO)

    # Verify to see if the path exists
    if os.path.isfile(args.path) is False:
        logging.error("{} cannot be found.".format(args.path))
        exit(1)

    # Open and read the contents of args.path
    with open(args.path) as file:
        process(yaml.load(file, Loader=yaml.FullLoader))


if __name__ == "__main__":
    main()
