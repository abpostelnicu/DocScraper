# DocScraper
Site scraper for different document types, easy to use and easy to configure.

# Install
We highly encourage to use the provided python3 virtual environment setup, in general this can be activated like:

``````shell
python3 -m venv $(pwd)/.venv/scraper

source .venv/scraper/bin/activate

pip3 install -r requirements.txt
``````

# Usage

The script uses a configuration `yaml`, the grammar of the configuration file is as follows:
* `sites` - list type
* `string` - element from the list that consists an identifier for each element
* `url` - string, the link of the site that is going to be scraped
* `limiter` - string, the domain in which the scraper will be ran, in general it's the same as `url`
* `path` - string, name of the folder under `${cwd}/documents` where the documents are going to be downloaded
* `documents` - list, strings that represent the extension of the documents

Example:

``````yaml
 sites:
  - my.site.name:
      url: https://some.site.com
      limiter: site.com
      path: site.com
      documents:
        - pdf
        - docx
        - doc
``````
