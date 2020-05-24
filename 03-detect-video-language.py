#!/usr/bin/env python
import csv
import argparse
from polyglot.detect import Detector
# 要pyicu,pycld2のインストール
# CFLAGS=-stdlib=libc++ pip install pycld2

def detect_language(title):
    title = ''.join(c for c in title if c.isprintable())
    detector = Detector(title, quiet=True)
    language = detector.language
    return language.code

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('in-file', type=argparse.FileType('r'),
                        help='csv file with cols that "video-id,title"')
    parser.add_argument('out-file', type=argparse.FileType('w'),
                        help='csv file added column "language"')

    args = parser.parse_args()
    ifp = args.__dict__['in-file']
    ofp = args.__dict__['out-file']

    csv_reader = csv.reader(ifp)
    header_row = next(csv_reader)
    title_col = header_row.index('title')
    vid_col = header_row.index('vid')

    csv_writer = csv.writer(ofp)
    csv_writer.writerow(header_row + ['language'])

    for row in csv_reader:
        vid, title = row[vid_col], row[title_col]
        language = detect_language(title)
        csv_writer.writerow(row + [language])

    ifp.close()
    ofp.close()

if __name__ == '__main__':
    main()
