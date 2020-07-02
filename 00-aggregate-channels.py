#!/usr/bin/env python
import re
import json
import argparse
from pathlib import Path

def extract_channel(path):
    datestr = path.parent.name
    m = re.match(
        r'([0-9]{4})([0-9]{2})([0-9]{2})-([0-9]{2})([0-9]{2})',
        datestr
    )
    if m is None:
        return []
    with open(path, 'r') as fp:
        try:
            contents = json.loads(fp.read())
        except:
            return []
    return [
        (datestr, i['snippet']['channelId']) for i in contents['items']
    ]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('in-dir', type=str)
    parser.add_argument('out-file', type=argparse.FileType('w'))
    args = parser.parse_args()

    in_dir = args.__dict__['in-dir']
    out_file = args.__dict__['out-file']

    trend_dir = '/Users/ysatotani/Desktop/YouTubeTrend-2020-06'
    p = Path(in_dir)
    channel_time = dict()
    for vf in sorted(p.glob('**/videos-*.json'), reverse=True):
        for time, cid in extract_channel(vf):
            channel_time[cid] = time
    for cid, time in sorted(channel_time.items(), key=lambda t: t[1]):
        print(time, cid, file=out_file)

if __name__ == '__main__':
    main()
