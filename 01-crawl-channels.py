#!/usr/bin/env python
import time
from urllib.parse import urlparse
from selenium import webdriver

def find_video_ids_from(driver):
    links = set(map(
        lambda a: a.get_attribute('href'),
        driver.find_elements_by_xpath('//a[contains(@href, "/watch")]')
    ))
    vids = set(filter(None, map(lambda p: p.get('v', None), map(
        lambda link: dict(
            p.split('=') for p in urlparse(link)[4].split('&')
        ),
        links
    ))))
    return vids

def find_thumbnail_dict_from(driver):
    imgs_url = set(map(
        lambda a: a.get_attribute('src'),
        driver.find_elements_by_xpath('//img[contains(@src, "i.ytimg.com")]')
    ))
    imgs = dict(map(
        lambda i: (urlparse(i)[2].split('/')[-2], i.split('?')[0]),
        imgs_url
    ))
    return imgs

def find_title_dict_from(driver):
    return dict(map(
        lambda a: (
            dict(
                q.split('=') for q in
                urlparse(a.get_attribute('href'))[4].split('&')
                if len(q.split('=')) == 2
            ).get('v', ''),
            a.text
        ),
        driver.find_elements_by_xpath('//a[contains(@href, "/watch")]')
    ))

def fetch_title_and_thumbnails(driver, channel_id, n_thumbnails=50):
    driver.get(f'https://www.youtube.com/channel/{channel_id}/videos')
    elements = dict()
    scroll_progress = True
    while len(elements) < n_thumbnails and scroll_progress:
        offset_prev = driver.execute_script('return window.pageYOffset')
        time.sleep(0.1)
        for _ in range(25):
            driver.execute_script(f'window.scrollBy(0,100)')
            time.sleep(0.1)
        offset_curr = driver.execute_script('return window.pageYOffset')
        time.sleep(0.1)
        if offset_curr == offset_prev:
            scroll_progress = False

        vids = find_video_ids_from(driver)
        thumbs = find_thumbnail_dict_from(driver)
        titles = find_title_dict_from(driver)
        elements = dict(
            (vid, (titles[vid], thumbs[vid]))
            for vid in vids
            if vid in thumbs and vid in titles
        )
    return elements

def main():
    import sys
    import csv
    in_file = sys.argv[1]
    with open(in_file, 'r') as fp:
        channels = set(fp.read().splitlines())
    if len(sys.argv) > 2:
        exclude_file = sys.argv[2]
        with open(exclude_file, 'r') as fp:
            channels.difference_update(fp.read().splitlines())

    driver = webdriver.Safari()
    driver.maximize_window()

    with open('all-videos.csv', 'w', newline='') as ofp:
        writer = csv.writer(ofp)
        writer.writerow(['vid', 'cid', 'title', 'thumbnail-url'])
        for cid in sorted(channels):
            elements = fetch_title_and_thumbnails(driver, cid)
            for vid, (title, url) in elements.items():
                writer.writerow([vid, cid, title.replace('\n', '\\n'), url])

    driver.close()

if __name__ == '__main__':
    main()
