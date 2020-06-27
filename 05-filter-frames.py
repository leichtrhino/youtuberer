#!/usr/bin/env python
import os
import re
import math
import pickle
import argparse
import tempfile
import subprocess

import numpy as np
import scipy.signal
import torch
import torchaudio

def calculate_confidence(activesd_path):
    with open(activesd_path, 'rb') as fp:
        dists = pickle.load(fp)
    framewise_confidences, confidences = [], []
    for dist in dists:
        mean_dist = np.mean(dist, 0)
        minval = np.min(mean_dist)
        minidx = np.argmin(mean_dist)
        conf = np.median(mean_dist) - minval
        framewise_conf = np.median(mean_dist) - dist[:, minidx]
        framewise_conf_m = scipy.signal.medfilt(framewise_conf, kernel_size=9)
        framewise_confidences.append(framewise_conf_m)
        confidences.append(conf)
    return framewise_confidences, confidences

def calculate_rms_db(video_path, frame_rate):
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, 'audio.wav')
        subprocess.run([
            'ffmpeg', '-i', video_path, '-vn', '-acodec', 'copy', audio_path
        ])
        x, sr = torchaudio.load(audio_path)
    n_samples_per_frame = int(sr / frame_rate)
    n_frames = int(x.shape[1] / n_samples_per_frame)
    x = x[0][:n_frames*n_samples_per_frame]\
        .reshape(n_frames, n_samples_per_frame)
    rmse = x.norm(p=2, dim=-1) / math.sqrt(n_samples_per_frame)
    rms_db = 20 * torch.log10(rmse)
    return rms_db.numpy()

def process_video(vid, args):
    frame_rate = 25
    if args.verbose:
        print(f'processing {vid}')

    syncnet_output_dir = args.__dict__['syncnet-output-dir']
    pycrop_dir = os.path.join(syncnet_output_dir, 'pycrop')
    pywork_dir = os.path.join(syncnet_output_dir, 'pywork')
    activesd_path = os.path.join(pywork_dir, vid, 'activesd.pckl')
    filtered_output_dir = args.__dict__['filtered-output-dir']
    outpycrop_dir = os.path.join(filtered_output_dir, vid)
    if not os.path.isdir(filtered_output_dir):
        os.mkdir(filtered_output_dir)
    if not os.path.isdir(outpycrop_dir):
        os.mkdir(outpycrop_dir)
    if not os.path.isfile(activesd_path):
        if args.error_noexist:
            raise RuntimeError(f'video {vid} does not have activesd.pckl')
        else:
            if args.verbose:
                print('video {vid} does not have activesd.pckl, skip.')
                return
    # 1. calculate framewise confidence score for all crops
    framewise_confidences, confidences = calculate_confidence(activesd_path)
    # 2. calculate rms in db
    rms_dbs = list()
    video_dir = os.path.join(pycrop_dir, vid)
    video_files = sorted(os.listdir(video_dir))
    for video_file in video_files:
        video_path = os.path.join(video_dir, video_file)
        rms_db = calculate_rms_db(video_path, frame_rate=frame_rate)
        rms_dbs.append(rms_db)
    # 3. find active segments
    segments = list()
    for i, (confidence, rms_db) in enumerate(zip(confidences, rms_dbs)):
        is_onset = False
        for j, (c, d) in enumerate(zip(confidence, rms_db)):
            if not is_onset and\
               (c >= args.confidence_threshold or d <= args.silence_threshold):
                is_onset = True
                segment_start = j
            elif is_onset and\
                 (c < args.confidence_threshold and d > args.silence_threshold):
                is_onset = False
                segment_end = j
                segments.append((i, segment_start, segment_end))
        if is_onset:
            segments.append((i, segment_start, len(confidence)))
    # 4. merge segments
    if len(segments) > 0:
        _segments, segments = segments, []
        last_segment = next(iter(_segments))
        for i, ss, sg in _segments[1:]:
            if i != last_segment[0] or\
               (ss - last_segment[2] - 1) / frame_rate > args.max_merge_gap:
                # push last segment
                segments.append(last_segment)
                last_segment = (i, ss, sg)
            else:
                # merge segment
                last_segment = (i, last_segment[1], sg)
        # push last segment
        segments.append(last_segment)
    # 5. filter short or silence segments
    segments = list(filter(
        lambda t: np.sum(rms_dbs[t[0]][t[1]:t[2]+1] >= args.silence_threshold)
        >= frame_rate * args.min_length,
        segments
    ))
    # 6. save
    if not os.path.isdir(outpycrop_dir):
        os.mkdir(outpycrop_dir)
    for i, (j, ss, sg) in enumerate(segments):
        in_video_path = os.path.join(video_dir, video_files[j])
        out_video_path = os.path.join(outpycrop_dir, f'{i:06d}.avi')
        subprocess.run([
            'ffmpeg',
            '-ss', str(ss / frame_rate),
            '-i', in_video_path,
            '-to', str((sg - ss + 1) / frame_rate),
            '-c', 'copy', out_video_path
        ])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--confidence-threshold', type=float, default=5.)
    parser.add_argument('--silence-threshold', type=float, default=-40)
    parser.add_argument('--min-length', type=float, default=2.)
    parser.add_argument('--max-merge-gap', type=float, default=0.24)
    parser.add_argument('--error-noexist', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('syncnet-output-dir')
    parser.add_argument('filtered-output-dir')

    args = parser.parse_args()
    syncnet_output_dir = args.__dict__['syncnet-output-dir']
    pywork_dir = os.path.join(syncnet_output_dir, 'pywork')
    pycrop_dir = os.path.join(syncnet_output_dir, 'pycrop')
    filtered_output_dir = args.__dict__['filtered-output-dir']

    video_ids = list(filter(
        lambda x: re.match(r'[\w\-]{8,12}', x),
        set(os.listdir(pywork_dir)) & set(os.listdir(pycrop_dir))
    ))

    for vid in video_ids:
        process_video(vid, args)

if __name__ == '__main__':
    main()
