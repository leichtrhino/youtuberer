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
    in_file = 'videos-face-20200507.csv'
    out_file = 'videos-facelang-20200507.csv'
    with open(in_file, 'r') as ifp, open(out_file, 'w') as ofp:
        csv_reader = csv.reader(ifp)
        header_row = next(csv_reader)
        ncol = len(header_row)
        title_col = header_row.index('title')
        vid_col = header_row.index('vid')

        csv_writer = csv.writer(ofp)
        csv_writer.writerow(header_row + ['language'])

        for row in csv_reader:
            vid, title = row[vid_col], row[title_col]
            language = detect_language(title)
            csv_writer.writerow(row + [language])

if __name__ == '__main__':
    main()
