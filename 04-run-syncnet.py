#!/usr/bin/env python
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import sys
import shutil
import tempfile
import subprocess

import pafy

def process_video(vid):
    with tempfile.TemporaryDirectory() as tmpdirname:
        # fetch video
        video = max(
            (v for v in pafy.new(vid).streams if v.extension == 'mp4'),
            key=lambda v: int(v.resolution.split('x')[0])
        )
        video_path = os.path.abspath(
            os.path.join(tmpdirname, f'{vid}.{video.extension}'))
        video.download(filepath=video_path)
        # run syncnet pipeline
        syncnet_output = os.path.abspath('./syncnet_output')
        syncnet_option = [
            '--videofile', video_path,
            '--reference', vid,
            '--data_dir', syncnet_output,
        ]
        os.chdir('syncnet_python')
        subprocess.run(['python', 'run_pipeline.py'] + syncnet_option)
        subprocess.run(['python', 'run_syncnet.py'] + syncnet_option)
        subprocess.run(['python', 'run_visualise.py'] + syncnet_option)
        os.chdir('..')
        # cleanup to remove full video
        for dirname in ('pyavi', 'pyframes', 'pytmp'):
            shutil.rmtree(os.path.join(syncnet_output, dirname))

def main():
    pafy.set_api_key('')
    process_video('8rl14iNf-ug')

if __name__ == '__main__':
    main()
