#!/usr/bin/env python
import csv
import urllib
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
    import sys
    in_file = 'all-videos-20200507.csv'
    out_file = 'videos-face-20200507.csv'
    with open(in_file, 'r') as ifp, open(out_file, 'w') as ofp:
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
            sys.stdout.write(f'\r{n_rows}')

if __name__ == '__main__':
    main()
