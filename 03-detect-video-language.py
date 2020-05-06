#!/usr/bin/env python
import csv
from polyglot.detect import Detector
# 要pyicu,pycld2のインストール
# CFLAGS=-stdlib=libc++ pip install pycld2

def detect_language(title):
    title = ''.join(c for c in title if c.isprintable())
    detector = Detector(title, quiet=True)
    language = detector.language
    return language.code

def main():
    in_file = 'channel-videos-512.csv'
    out_file = 'video-language.csv'
    with open(in_file, 'r') as ifp, open(out_file, 'w') as ofp:
        csv_reader = csv.reader(ifp)
        header_row = next(csv_reader)
        ncol = len(header_row)
        title_col = header_row.index('title')
        vid_col = header_row.index('vid')

        print('vid,language', file=ofp)
        for vid, title in map(lambda r: (r[vid_col], r[title_col]), csv_reader):
            language = detect_language(title)
            print(f'{vid},{language}', file=ofp)

if __name__ == '__main__':
    main()
