
import re
import os
import argparse
import pickle
import numpy as np

def calculate_confidence(pywork_dir, vid):
  activesd_path = os.path.join(pywork_dir, vid, 'activesd.pckl')
  if not os.path.isfile(activesd_path):
    return []
  with open(activesd_path, 'rb') as fp:
    dists = pickle.load(fp)
  confidences = []
  for dist in dists:
    mean_dist = np.mean(dist, 0)
    minval = np.min(mean_dist)
    minidx = np.argmin(mean_dist)
    conf = np.median(mean_dist) - minval
    confidences.append(conf)
  return confidences, list(d.shape[0] / 25 for d in dists)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('in-dir', type=str)
    parser.add_argument('out-file', type=argparse.FileType('w'))
    args = parser.parse_args()

    syncnet_out_dir = args.__dict__['in-dir']
    pywork_dir = os.path.join(syncnet_out_dir, 'pywork')

    vids = list(filter(lambda x: re.match(r'[\w\-]{8,12}', x), os.listdir(pywork_dir)))
    header = 'scene,score,length'
    body = '\n'.join(
        f'{v}/{i:05}.avi,{s},{l}'
        for v in vids
        for i, (s, l) in enumerate(zip(*calculate_confidence(pywork_dir, v)))
    )

    out_file = args.__dict__['out-file']
    print(header, file=out_file)
    print(body, file=out_file)

if __name__ == '__main__':
    main()
