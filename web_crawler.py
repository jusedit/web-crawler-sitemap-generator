import time
from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup
import os
from xml.etree import ElementTree as ET
from urllib.parse import urljoin
import requests
from datetime import datetime
import xml.dom.minidom


# Initialize the WebDriver with the GeckoDriverManager
options = webdriver.FirefoxOptions()
options.headless = True
driver = webdriver.Firefox(executable_path=GeckoDriverManager().install(), options=options)

# Keep track of visited URLs to prevent duplicates
visited_urls = set()
found_urls = set()
def get_last_modified_header(url):
    try:
        response = requests.head(url)
        last_modified = response.headers.get('Last-Modified')
        if last_modified:
            # Convert the last modified date to the desired format
            last_modified_datetime = datetime.strptime(last_modified, "%a, %d %b %Y %H:%M:%S GMT")
            last_modified_formatted = last_modified_datetime.strftime("%Y-%m-%dT%H:%M:%S+00:00")
            return last_modified_formatted
        else:
            return "Last-Modified header not found in the response headers."
    except requests.exceptions.RequestException as e:
        # Use the current time in the desired format
        current_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")
        return f"Error: {str(e)} (Using current time: {current_time})"
# Function to recursively crawl the webpage and generate a sitemap
def crawl_and_generate_sitemap(base_url, url, cdepth=10):
    if url.startswith("/"):
        full_link = urljoin(base_url, url)
    else:
        full_link = url
    if full_link.startswith("mailto:") or full_link.startswith("tel:"):
        return
    if not base_url in full_link:
        return
    if cdepth == 0 or full_link in visited_urls:
        return
    visited_urls.add(full_link)
    driver.get(full_link)
    print(f"Current: {full_link}")
    print(f"Visited {len(visited_urls)} unique URLs.")
    time.sleep(2)  # Add a delay to allow the page to load (adjust as needed)

    # Parse the page content with BeautifulSoup
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    # Get the canonical link or use full_link if not present
    canonical_link = soup.find('link', {'rel': 'canonical'})
    if canonical_link and canonical_link['href'] != full_link:
        print("Skip to canonical")
        crawl_and_generate_sitemap(base_url, canonical_link['href'], cdepth)
        return
    else:
        canonical_url = full_link


    # Generate priority
    priority = cdepth / depth;

    # Create a URL element for the sitemap and append it to the sitemap_root
    url_element = ET.SubElement(sitemap_root, "url")
    loc_element = ET.SubElement(url_element, "loc")
    loc_element.text = canonical_url
    lastmod_element = ET.SubElement(url_element, "lastmod")
    lastmod_element.text = get_last_modified_header(full_link)
    priority_element = ET.SubElement(url_element, "priority")
    priority_element.text = str(priority)

    # Recursively crawl the linked pages
    links = [a['href'] for a in soup.find_all('a', href=True)]
    new_urls = set()
    for link in links:
        if not link in found_urls:
            new_urls.add(link)
            found_urls.add(link)
    for link in new_urls:
        crawl_and_generate_sitemap(base_url, link, cdepth - 1)

# Ask the user to input the starting URL
start_url = input("Enter the starting URL: ")

# Create the sitemap XML root element
sitemap_root = ET.Element("urlset")
sitemap_namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"  # Replace with the desired namespace
sitemap_root = ET.Element("urlset", xmlns=sitemap_namespace)

# Start crawling
depth = 10
crawl_and_generate_sitemap(start_url, start_url, depth)

# Save the sitemap data to an XML file
sitemap_tree = ET.ElementTree(sitemap_root)
sitemap_tree.write("sitemap.xml")

# Format the XML to make it human-readable
with open("sitemap.xml", "r") as xml_file:
    xml_content = xml_file.read()
    parsed_xml = xml.dom.minidom.parseString(xml_content)
    formatted_xml = parsed_xml.toprettyxml()

with open("sitemap.xml", "w") as xml_file:
    xml_file.write(formatted_xml)

# Close the WebDriver when done
driver.quit()

# Display user-friendly output
print("Crawling and sitemap generation complete.")
print(f"Visited {len(visited_urls)} unique URLs.")
print("Sitemap saved to sitemap.xml.")
