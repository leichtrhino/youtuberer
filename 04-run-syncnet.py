#!/usr/bin/env python
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import sys
import csv
import shutil
import tempfile
import subprocess
import random
import argparse

import pafy
pafy.set_api_key('')

def process_video(vid, target_dir):
    if os.path.exists(os.path.join(target_dir, 'pycrop', vid)):
        print(f'Video {vid} already processed. skip.')
        return
    print(f'Processing {vid}')
    os.chdir('syncnet_python')
    with tempfile.TemporaryDirectory() as tmpdirname:
        # fetch video
        video = max(
            (v for v in pafy.new(vid).streams if v.extension == 'mp4'),
            key=lambda v: int(v.resolution.split('x')[0])
        )
        video_path = os.path.join(tmpdirname, f'{vid}.{video.extension}')
        video.download(filepath=video_path)
        # run syncnet pipeline
        syncnet_option = [
            f'--videofile={video_path}',
            f'--reference={vid}',
            f'--data_dir={tmpdirname}',
        ]
        subprocess.run(['python', 'run_pipeline.py'] + syncnet_option)
        subprocess.run(['python', 'run_syncnet.py'] + syncnet_option)
        subprocess.run(['python', 'run_visualise.py'] + syncnet_option)
        # copy output
        for dirname in ('pycrop', 'pywork'):
            shutil.copytree(os.path.join(tmpdirname, dirname, vid),
                            os.path.join('..', target_dir, dirname, vid))

    os.chdir('..')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('in-file', type=argparse.FileType('r'))
    parser.add_argument('out-dir', type=str)

    args = parser.parse_args()
    ifp = args.__dict__['in-file']
    target_dir = args.__dict__['out-dir']

    reader = csv.reader(ifp)
    header_row = next(reader)
    vid_col = header_row.index('vid')
    rows = [row for row in reader]
    random.shuffle(rows)

    for row in rows:
        vid = row[vid_col]
        process_video(vid, target_dir)

    ifp.close()

if __name__ == '__main__':
    main()
