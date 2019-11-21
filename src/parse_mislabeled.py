import argparse
import os.path as osp
import json


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list_path', type=str, help='Input file list to be parsed')
    parser.add_argument('--output_path', type=str, help='Output file where the parsed data is stored')
    parser.add_argument('--dataturks_path', type=str, help='JSON output file where dataturks annotation is stored')
    parser.add_argument('--media_url', type=str, default='http://vid-gpu6.inf.cs.cmu.edu:9000', help='')
    return parser.parse_args()


def extract_data(file_path):
    file_name, file_ext = osp.splitext(osp.basename(file_path))
    tokens = file_name.split('_')
    camera_id = tokens[0].split('.')[-1]
    action_class = ('_'.join(tokens[2:-1])).lower()
    return camera_id, action_class


def main(args):
    list_path = args.list_path
    file_list = [l.strip() for l in open(list_path, 'r').readlines()]
    camera_list, class_list  = zip(*list(map(extract_data, file_list)))

    # Write CSV output
    with open(args.output_path, 'a+') as output_file:
        for file_path, camera_id, video_class in zip(file_list, camera_list, class_list):
            output_file.write(f'{file_path},{camera_id},{video_class}\n')

    # Write DataTurks CSV output
    with open(args.dataturks_path, 'a+') as json_file:
        sample_id = 1
        for file_path, camera_id, video_class in zip(file_list, camera_list, class_list):
            file_url = osp.join(args.media_url, file_path[2:])
            json_file.write(f'{file_url}\t{video_class}\tid={sample_id}\tnote={video_class}\n')
            sample_id += 1


if __name__ == '__main__':
    args = parse_args()
    main(args)