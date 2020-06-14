#!/usr/bin/env python
import os
import re
import math
import pickle
import argparse

import numpy as np
import scipy.signal
import torch
import torchvision.io

from facenet_pytorch import InceptionResnetV1

def calculate_confidence(activesd_path):
    with open(activesd_path, 'rb') as fp:
        dists = pickle.load(fp)
    confidences = []
    for dist in dists:
        mean_dist = np.mean(dist, 0)
        minval = np.min(mean_dist)
        minidx = np.argmin(mean_dist)
        conf = np.median(mean_dist) - minval
        framewise_conf = np.median(mean_dist) - dist[:, minidx]
        framewise_conf_m = scipy.signal.medfilt(framewise_conf, kernel_size=9)
        confidences.append({'conf': conf, 'framewise-conf': framewise_conf_m})
    return confidences

def calculate_embedding(video_path, model, device):
    vframes, _, _ = torchvision.io.read_video(video_path)
    vframes = vframes.to(device)
    frames = vframes.permute((0, 3, 1, 2)).float().div(255)
    frames = torch.nn.functional.interpolate(frames, (160, 160))
    embedding_vectors = model(frames).detach()
    return embedding_vectors.to('cpu').numpy()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', default='cpu')
    parser.add_argument('--without-embedding', action='store_true')
    parser.add_argument('--without-confidence', action='store_true')
    parser.add_argument('--ignore-noexist', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('syncnet-output-dir')

    args = parser.parse_args()
    syncnet_output_dir = args.__dict__['syncnet-output-dir']
    pywork_dir = os.path.join(syncnet_output_dir, 'pywork')
    pycrop_dir = os.path.join(syncnet_output_dir, 'pycrop')
    video_ids = list(filter(
        lambda x: re.match(r'[\w\-]{8,12}', x),
        set(os.listdir(pywork_dir)) & set(os.listdir(pycrop_dir))
    ))

    device = torch.device(args.device)
    model = InceptionResnetV1(pretrained='vggface2').eval().to(device)

    for vid in video_ids:
        if args.verbose:
            print(f'processing {vid}')
        if not args.without_confidence:
            activesd_path = os.path.join(pywork_dir, vid, 'activesd.pckl')
            if args.ignore_noexist and not os.path.isfile(activesd_path):
                continue
            confidence_file = os.path.join(pywork_dir, vid, 'confidence.pckl')
            confidence = calculate_confidence(activesd_path)
            with open(confidence_file, 'wb') as fp:
                pickle.dump(confidence, fp)

        if not args.without_embedding:
            scene_names = sorted(os.listdir(os.path.join(pycrop_dir, vid)))
            get_scene_file = lambda x: os.path.join(pycrop_dir, vid, x)
            embedding_file = os.path.join(pywork_dir, vid, 'embeddings.pckl')
            embeddings = [
                calculate_embedding(get_scene_file(scene_name), model, device)
                for scene_name in scene_names
            ]
            with open(embedding_file, 'wb') as fp:
                pickle.dump(embeddings, fp)

if __name__ == '__main__':
    main()
