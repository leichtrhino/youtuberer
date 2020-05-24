#!/usr/bin/env python
import sys
import csv
import urllib
import argparse
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1

mtcnn = MTCNN()
def count_faces_of(url):
    try:
        img = Image.open(urllib.request.urlopen(url))
    except:
        return 0
    #img_cropped = mtcnn(img) # detect and crop
    boxes, probs = mtcnn.detect(img, landmarks=False)
    #boxes, probs, points = mtcnn.detect(img, landmarks=True)
    return boxes.shape[0] if boxes is not None else 0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('in-file', type=argparse.FileType('r'),
                        help='csv file has cols of "video-id,thumbnail-url"')
    parser.add_argument('out-file', type=argparse.FileType('w'),
                        help='csv file added column "n-faces"')

    args = parser.parse_args()
    ifp = args.__dict__['in-file']
    ofp = args.__dict__['out-file']
    verbose = args.verbose

    csv_reader = csv.reader(ifp)
    header_row = next(csv_reader)
    ncol = len(header_row)
    url_col = header_row.index('thumbnail-url')
    vid_col = header_row.index('vid')

    csv_writer = csv.writer(ofp)
    csv_writer.writerow(header_row + ['n-faces'])

    n_rows = 0
    for row in csv_reader:
        vid, url = row[vid_col], row[url_col]
        n_rows += 1
        nfaces = count_faces_of(url)
        csv_writer.writerow(row + [nfaces])
        if verbose:
            sys.stdout.write(f'\r{n_rows}')

    ifp.close()
    ofp.close()

if __name__ == '__main__':
    main()
