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

def fetch_image_urls(state_query):
    query=state_query["query"]
    max_links_to_fetch=state_query["max_links_to_fetch"]
    wd=state_query["webdriver"]
    sleep_between_interactions=state_query["sleep_between_interactions"]
    
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

        if len(thumbnail_results[results_start:number_results])==0:
            print("Looks like you've reached the end")
            break
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
                break
            else:
                # executing the show more results tab
                load_more_button = wd.find_element_by_css_selector(".mye4qd")
                if load_more_button:
                    #print("executing")
                    wd.execute_script("document.querySelector('.mye4qd').click();")

        # move the result startpoint further down
        results_start = len(thumbnail_results)

    return image_urls


def persist_image(state_link,query,f):
  

    print(state_link["url"])
    image_content = requests.get(state_link["url"],stream=True).content
    image_file = io.BytesIO(image_content)
    try:
        image = Image.open(image_file).convert('RGB')
        image.save(state_link["file_path"])
        f.write(state_link["file_path"].split('/')[-1][:-4] + " " + state_link["url"] + "\n")
        return f
    except:
        return f
        



# NEED TO DOWNLOAD CHROMEDRIVER, insert path to chromedriver inside parentheses in following line
wd = webdriver.Chrome('/usr/local/bin/chromedriver')
save_dir = './images/'
queries = ["dented cars", "scratched cars"]  #change your set of querries here
max_img_per_query=1500
state_query=dict()
state_link=dict()
for query in queries:
    if not os.path.exists(os.path.join(save_dir,query.replace(" ","-"))):
        os.makedirs(os.path.join(save_dir,query.replace(" ","-")))

    f=open(os.path.join(save_dir,query.replace(" ","-")+'.txt'),'w')
    wd.get('https://google.com')
    search_box = wd.find_element_by_css_selector('input.gLFyf')
    search_box.send_keys(query)
    state_query["query"]=query
    state_query["max_links_to_fetch"]=max_img_per_query
    state_query["webdriver"]=wd
    state_query["sleep_between_interactions"]=0.1
    links = fetch_image_urls(state_query)
    
    for i,link in enumerate(links):
       
        state_link["url"]=link
        state_link["file_path"]=os.path.join(save_dir,query.replace(" ","-"),str(i).zfill(5) + '.jpg')
        f = persist_image(state_link,query,f)
    
    f.close()
wd.quit()
print("Done")
