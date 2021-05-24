import argparse
import logging
import os
import re
from urllib.parse import urlparse

import wget
import yaml
from selenium import webdriver

already_visited = dict()

logger = logging.getLogger("doc-scraper")


def download(link, definition, spaces):
    """Download utility from an url.

    :param link: path for of the file that is going to be downloaded
    :param definition: definition from the config file, in order to determine
    path where the downloaded file will be stored
    :return:  1 on failure, 0 otherwise
    """

    # extract the filename
    filename = os.path.basename(urlparse(link).path)

    # Create path
    path = os.path.join(os.path.abspath(os.getcwd()), "documents", definition["path"])

    # Create dirs
    os.makedirs(path, exist_ok=True)

    try:
        logger.info(spaces + "-> Downloading {0}".format(filename))
        wget.download(link, os.path.join(path, filename), bar=None)
    except Exception as e:
        logger.error(
            spaces + "-> Unable to download {0} with error {1}".format(link, e)
        )
        return 1

    return 0


def has_document(link, definition):

    for doc in definition["documents"]:
        if link.lower().endswith(doc.lower()):
            return True


def process_site(site_limit, url, definition, driver, spaces=""):
    try:
        driver.get(url)
    except Exception as _:
        logger.error("Exception for {}".format(url))
        return

    elements = driver.find_elements_by_xpath("//a[@href]")

    links = list()

    # Cache hrefs since dom is going to be modified once we do driver.geturl(...)
    for elem in elements:
        retries = 4
        href = None
        while retries > 0:
            try:
                href = elem.get_attribute("href")
                break
            except Exception as _:
                pass

        if href is not None and len(href) > 0:
            links.append(elem.get_attribute("href"))

    for href in links:
        # Did we analyze this?
        if already_visited.get(href, None) is not None:
            # yes we did
            continue
        already_visited[href] = True

        logger.info(spaces + "-> Analyze for: {}".format(href))

        if has_document(href, definition):
            logger.info(spaces + "-> Found document: {}".format(href))
            download(href, definition, spaces)
        else:
            # Do not cross-site
            if re.search(site_limit, href) is None:
                logger.info(spaces + "-> Skip {}".format(href))
                continue
            process_site(site_limit, href, definition, driver, spaces + " ")


def get_driver_options(driver_options):
    driver_options.headless = True

    return driver_options


def process(yml):
    sites = yml.get("sites", None)
    if sites is None:
        logger.error("`sites` from yaml config file is empty, nothing to do.")
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
            logger.error("Unable to init web driver, tried Firefox and Chrome.")
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

    # create formatter
    formatter = logging.Formatter("%(message)s")

    logger.setLevel(logging.DEBUG)

    # create console handler and set level to info
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # create formatter
    formatter = logging.Formatter("%(message)s")

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

    # Verify to see if the path exists
    if os.path.isfile(args.path) is False:
        logger.error("{} cannot be found.".format(args.path))
        exit(1)

    # Open and read the contents of args.path
    with open(args.path) as file:
        process(yaml.load(file, Loader=yaml.FullLoader))


if __name__ == "__main__":
    main()
