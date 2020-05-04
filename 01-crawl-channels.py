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
    with open('channel-id.txt', 'r') as fp:
        channels = fp.read().splitlines()

    driver = webdriver.Safari()
    driver.maximize_window()

    with open('channel-videos.csv', 'w') as ofp:
        print('cid,vid,title,thumbnail-url', file=ofp)
        for cid in channels[:512]:
            elements = fetch_title_and_thumbnails(driver, cid)
            for vid, (title, url) in elements.items():
                print(
                    repr('{},{},"{}",{}'.format(
                        cid, vid, title.replace('"', '""'), url
                    )),
                    file=ofp
                )

    driver.close()

if __name__ == '__main__':
    main()
