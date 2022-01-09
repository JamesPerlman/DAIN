import argparse
import os
from pathlib import Path

from interpolate_video import dain_slowmotion

# Parse command line arguments

parser = argparse.ArgumentParser(description="BATCH_DAIN")

parser.add_argument("-i", "--in_file", type=str, required=True)
parser.add_argument("-o", "--out_file", type=str, required=True)
parser.add_argument("--slow", type=int, default=8)
parser.add_argument("--loop", type=bool, default=False)
parser.add_argument("--fps", type=int, default=0)

args = parser.parse_args()

in_path = Path(args.in_file)
out_path = Path(args.out_file)

# Run DAIN on a single file or a directory

if os.path.isfile(in_path):
    dain_slowmotion(
        input_file_path=in_path,
        output_dir_path=out_path,
        slow_factor=args.slow,
        seamless=args.loop,
        output_fps=args.fps
    )
else:
    for filename in os.listdir(in_path):
        in_file = in_path / filename
        
        if not os.path.isfile(in_file):
            continue

        dain_slowmotion(
            input_file_path=in_file,
            output_dir_path=out_path,
            slow_factor=args.slow,
            seamless=args.loop,
            output_fps=args.fps
        )

print(f"Your files are ready! Please check out {out_path} for results.")
