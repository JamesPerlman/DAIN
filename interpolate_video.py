import os
from pathlib import Path
import shutil
import subprocess as sp

def dain_slowmotion(
    input_filepath: Path,
    output_dir: Path,
    slow_factor: int,
    seamless: bool = False,
    output_fps: int = 0,
    dain_exec_path: Path = Path("/usr/local/dain/colab_interpolate.py")
):
    # Make the output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Make input frames directory
    input_frames_dir = output_dir / "input_frames"
    shutil.rmtree(input_frames_dir, ignore_errors=True)
    input_frames_dir.mkdir()
    print(f"Created directory for input frames: {input_frames_dir}")

    # Make output frames directory
    output_frames_dir = output_dir / "output_frames"
    shutil.rmtree(output_frames_dir, ignore_errors=True)
    output_frames_dir.mkdir()
    print(f"Created directory for output frames: {output_frames_dir}")

    # Use ffmpeg to extract input frames
    print("Extracting input frames...")
    os.system(f"ffmpeg -i '{input_filepath}' '{input_frames_dir}/%05d.png'")
    print("Input frames have been extracted.")

    # Assign input properties
    input_frames = [name for name in os.listdir(input_frames_dir) if os.path.isfile(input_frames_dir / name)]
    num_input_frames = len(input_frames)
    first_input_frame = input_frames_dir / f"{1:05d}.png"

    # Detect and remove alpha channel if necessary
    img_channels = sp.getoutput('identify -format %[channels] 00001.png')
    
    if "a" in img_channels:
        print("Detected alpha channel in input frames.  Removing.")
        print(sp.getoutput(f"find '{input_frames_dir}' -name '*.png' -exec convert '{{}}' -alpha off PNG24:'{{}}' \\;"))
        print("Each image has had its alpha channel removed.")

    # Use first frame as last if this is a looping video
    if seamless:
        num_input_frames += 1
        loop_input_frame = input_frames_dir / f"{num_input_frames:05d}.png"
        shutil.copy(first_input_frame, loop_input_frame)
        print("Using first frame as last frame.")
    
    # Interpolate with DAIN
    time_step = 1 / float(slow_factor)
    os.system(
        f" \
            python {dain_exec_path} \
            --netName DAIN_slowmotion \
            --time_step {time_step} \
            --start_frame 1 \
            --end_frame {num_input_frames} \
            --frame_input_dir '{input_frames_dir}' \
            --frame_output_dir '{output_frames_dir}' \
        "
    )

    # Calculate output fps
    input_fps_str = sp.getoutput(f"ffprobe -v 0 -of csv=p=0 -select_streams v:0 -show_entries stream=r_frame_rate {input_filepath}")
    input_fps_n, input_fps_d = [int(n) for n in input_fps_str.split("/")]
    
    output_fps_n = input_fps_n / time_step
    output_fps_d = input_fps_d

    if output_fps < 1:
        output_fps_str = f"{output_fps_n}/{input_fps_d}"
        output_fps_int = int(input_fps_n)
    else:
        output_fps_str = str(output_fps)
        output_fps_int = output_fps

    # Generate output video
    output_video_path = output_dir / f"{input_filepath.stem}-{slow_factor}x-{output_fps_int}fps.mp4"
    os.system(f"ffmpeg -y -r {output_fps_str} -f image2 -pattern_type glob -i '{output_frames_dir}/*.png' -pix_fmt yuv420p '{output_video_path}'")

dain_slowmotion(
    input_filepath=Path("/usr/local/dain/content/test1/books.mp4"),
    output_dir=Path("/usr/local/dain/content/test1-out"),
    slow_factor=16,
    output_fps=30,
    seamless=True
)
