import argparse
import os.path as osp
import json
import re
import subprocess
import ffmpeg
import shutil
from easydict import EasyDict as edict


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_path', type=str, help='Path to resulting json file from dataturks')
    parser.add_argument('--output_path', type=str, help='Path to output json file')
    parser.add_argument('--input_dir', type=str, help='Directory where the original videos are located')
    parser.add_argument('--output_dir', type=str, help='Directory where the refined videos will be saved')
    parser.add_argument('--media_url', type=str, default='http://vid-gpu6.inf.cs.cmu.edu:9000', help='')
    return parser.parse_args()


def get_label_from_path(file_path):
    file_name, file_ext = osp.splitext(osp.basename(file_path))
    tokens = file_name.split('_')
    action_label = ('_'.join(tokens[2:-1])).lower()
    return action_label


def is_timespan_string(input_str):
    return len(re.findall(r'\d+\.\d+-\d+\.\d+', input_str)) == 1


def sec2time(sec, n_msec=3):
    ''' Convert seconds to 'D days, HH:MM:SS.FFF' '''
    if hasattr(sec,'__len__'):
        return [sec2time(s) for s in sec]
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    if n_msec > 0:
        pattern = '%%02d:%%02d:%%0%d.%df' % (n_msec+3, n_msec)
    else:
        pattern = r'%02d:%02d:%02d'
    if d == 0:
        return pattern % (h, m, s)
    return ('%d days, ' + pattern) % (d, h, m, s)


def get_timespan_timecodes(input_str):
    start_time, end_time = [float(time_str) for time_str in re.findall(r'\d+\.\d+-\d+\.\d+', input_str)[0].split('-')]
    return sec2time(start_time), sec2time(end_time)


def get_video_duration(video_path):
    """Get the duration of a video using ffprobe."""
    cmd = f'ffprobe -i {video_path} -show_entries format=duration -v quiet -of csv="p=0"'
    output = subprocess.check_output(
        cmd,
        shell=True,
        stderr=subprocess.STDOUT
    )
    return float(output)


def trim_video(video_path, start_secs, end_secs, output_path):
    start_time = sec2time(start_secs)
    end_time = sec2time(end_secs)
    ffmpeg.input(video_path).trim(start='00:00:10.333', end='00:00:25.450').output(output_path).run()


def replace_label_in_filename(filename):


def get_csv_line(anno_dict):
    '''
    csv_line has the following fields [filename, original_label, new_labels, start_trim, end_trim, notes]
    it is tab separated since list of labels are comma separated
    5 states:
      1. ok
      2. relabel
      3. oktrim
      4. relabeltrim
      5. revisit
    :param anno_dict:
    :return:
    '''

    anno = edict(anno_dict)

    labels_agree = anno.original_label in anno.labels
    needs_trim = is_timespan_string(anno.notes)

    notes = anno.notes.strip()
    start_str = ''
    end_str = ''

    if needs_trim:
        start_str, end_str = get_timespan_timecodes(anno.notes)
        notes = ''

    if len(anno.labels) == 0:
        video_duration = get_video_duration(osp.join('/mnt/Alfheim/Data/MEVA/meva_viz_refine1/original', anno.filename))
        if video_duration < 1.0:
            notes = 'short clip'
        else:
            notes = 'revisit'

    # Process file
    if labels_agree and not needs_trim:
        video_path = osp.join(args.input_dir, anno.filename)
        shutil.copy2(video_path, args.output_dir)

    if not labels_agree and len(anno.labels) > 0:
        for label in anno.labels:
            if needs_trim:



    return f'{anno.filename},{anno.original_label},{"-".join(anno.labels)},{start_str},{end_str},{notes}'

def main(args):
    json_list = [edict(json.loads(l.strip())) for l in open(args.input_path, 'r').readlines()]

    output_list = []
    for anno in json_list:
        filename = osp.basename(anno.content)
        original_label = get_label_from_path(anno.content)
        if anno.annotation is None:
            labels = []
            notes = ''
        else:
            labels = anno.annotation['labels'] if 'labels' in anno.annotation else []
            notes = anno.annotation['note'] if 'note' in anno.annotation else ''

        anno_dict = dict(
            filename=filename,
            original_label=original_label,
            labels=labels,
            notes=notes
        )

        output_list.append(get_csv_line(anno_dict))

    with open(args.output_path, 'w') as output_file:
        output_file.write('\n'.join(output_list))

    print(f'Total clips: {len(output_list)}')



if __name__ == '__main__':
    args = parse_args()
    main(args)