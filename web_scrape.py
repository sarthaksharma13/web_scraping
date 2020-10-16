from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import json
import os
import urllib2
import argparse
import time
import io
import requests
from PIL import Image

def fetch_image_urls(state):
    query=state["query"]
    max_links_to_fetch=state["max_links_to_fetch"]
    wd=state["webdriver"]
    sleep_between_interactions=state["sleep_between_interactions"]
    
    def scroll_to_end(wd):
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep_between_interactions)    
    
    # build the google query
    search_url = "https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img"

    # load the page
    wd.get(search_url.format(q=query))

    image_urls = set()
    image_count = 0
    results_start = 0
    while image_count < max_links_to_fetch:
        scroll_to_end(wd)

        # get all image thumbnail results
        thumbnail_results = wd.find_elements_by_css_selector("img.Q4LuWd")
        number_results = len(thumbnail_results)
        
        #print(f"Found: {number_results} search results. Extracting links from {results_start}:{number_results}")
        
        for img in thumbnail_results[results_start:number_results]:
            # try to click every thumbnail such that we can get the real image behind it
            try:
                img.click()
                time.sleep(sleep_between_interactions)
            except Exception:
                continue

            # extract image urls    
            actual_images = wd.find_elements_by_css_selector('img.n3VNCb')
            for actual_image in actual_images:
                if actual_image.get_attribute('src') and 'http' in actual_image.get_attribute('src'):
                    image_urls.add(actual_image.get_attribute('src'))

            image_count = len(image_urls)

            if len(image_urls) >= max_links_to_fetch:
                #print(f"Found: {len(image_urls)} image links, done!")
                break
        else:
            #print("Found:", len(image_urls), "image links, looking for more ...")
            time.sleep(30)
            return
            load_more_button = wd.find_element_by_css_selector(".mye4qd")
            if load_more_button:
                wd.execute_script("document.querySelector('.mye4qd').click();")

        # move the result startpoint further down
        results_start = len(thumbnail_results)

    return image_urls

#(folder_path:str,file_name:str,url:str)
def persist_image(state):

    folder_path=state["folder_path"]
    query=state["query"]
    url=state["url"]
    file_name = state["file_name"]

    image_content = requests.get(url).content
    image_file = io.BytesIO(image_content)
    image = Image.open(image_file).convert('RGB')
    
    if os.path.exists(folder_path):
        file_path = os.path.join(folder_path,file_name + '.jpg')
    else:
        
        os.mkdir(folder_path)
        file_path = os.path.join(folder_path, file_name+ '.jpg')
    image.save(file_path)
    print("SUCCESS - saved")



# NEED TO DOWNLOAD CHROMEDRIVER, insert path to chromedriver inside parentheses in following line
wd = webdriver.Chrome('/usr/local/bin/chromedriver')

queries = ["CORONA-VIRUS"]  #change your set of querries here
state=dict()
for query in queries:
    wd.get('https://google.com')
    search_box = wd.find_element_by_css_selector('input.gLFyf')
    search_box.send_keys(query)
    #links = fetch_image_urls(query,2,wd)
    state["query"]=query
    state["max_links_to_fetch"]=1
    state["webdriver"]=wd
    state["sleep_between_interactions"]=1
    links = fetch_image_urls(state)
    save_dir = './images/'
    for i,link in enumerate(links):
        #persist_image(images_path,query,i)
        state_=dict()
        state_["folder_path"]=save_dir
        state_["query"]=query
        state_["url"]=link
        state_["file_name"]=str(i)
        persist_image(state_)
wd.quit()
