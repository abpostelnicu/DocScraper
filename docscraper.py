import requests
from urllib.request import unquote
import argparse
import yaml
import os
from selenium import webdriver
import validators
from urllib.parse import urlparse


already_visited = dict()


def download(link):
    document = requests.get(link)

    # extract  PDF file name
    filename = unquote(link.split("/")[-1].replace(" ", "_"))

    # write PDF to local file
    with open("./documents/" + filename, "wb") as f:
        # write PDF to local file
        f.write(document.content)


def has_document(link, definition):

    for doc in definition["documents"]:
        if link.lower().endswith(doc.lower()):
            return True


def process_site(site_name, url, definition, driver):
    try:
        driver.get(url)
    except Exception as _:
        print("Exception for {}".format(url))
        return

    elems = driver.find_elements_by_xpath("//a[@href]")

    links = list()

    # Cache hrefs since dom is going to be modified once we do driver.geturl(...)
    for elem in elems:
        href = elem.get_attribute("href")
        if len(href) > 0:
            links.append(elem.get_attribute("href"))

    for href in links:
        # Did we analyze this?
        if already_visited.get(href, None) is not None:
            # yes we did
            continue
        already_visited[href] = True

        print("Analyze for: {}".format(href))

        if has_document(href, definition):
            print("Found document: {}".format(href))
            download(href)
        else:
            # Do not cross-site
            # This is sub-optimal, should be redone
            if site_name not in href:
                print("Skip {}".format(href))
                continue
            process_site(site_name, href, definition, driver)


def process(yml):
    sites = yml.get("sites", None)
    if sites is None:
        exit(1)

    # Start selenium driver
    driver = webdriver.Firefox()

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

    # Verify to see if the path exists
    if os.path.isfile(args.path) is False:
        print("{} cannot be found.".format(args.path))

    # Open and read the contents of args.path
    with open(args.path) as file:
        process(yaml.load(file, Loader=yaml.FullLoader))


if __name__ == "__main__":
    main()