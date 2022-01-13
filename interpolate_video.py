import os
from pathlib import Path
import shutil
import subprocess as sp

def get_output_video_fps(
    input_file_path: Path,
    output_dir_path: Path,
    slow_factor: int,
    output_fps: int = 0,
) -> str:
    if output_fps > 0:
        return str(output_fps)
    
    input_fps_str = sp.getoutput(f"ffprobe -v 0 -of csv=p=0 -select_streams v:0 -show_entries stream=r_frame_rate {input_file_path}")
    input_fps_n, input_fps_d = [int(n) for n in input_fps_str.split("/")]
    
    output_fps_n = input_fps_n * slow_factor
    output_fps_d = input_fps_d

    return f"{output_fps_n}/{input_fps_d}"


def get_output_video_path(
    input_file_path: Path,
    output_dir_path: Path,
    slow_factor: int,
    output_fps_str: str
) -> str:
    output_fps_n, output_fps_d = [int(n) for n in output_fps_str.split("/")]
    output_fps_int = int(output_fps_n / output_fps_d)
    return output_dir_path / f"{input_file_path.stem}-{slow_factor}x-{output_fps_int}fps.mp4"


def dain_slowmotion(
    input_file_path: Path,
    output_dir_path: Path,
    slow_factor: int,
    seamless: bool = False,
    output_fps: int = 0,
    dain_exec_path: Path = Path("/usr/local/dain/colab_interpolate.py")
):
    # Get output details
    output_fps_str = get_output_video_fps(input_file_path, output_dir_path, slow_factor, output_fps)
    output_video_path = get_output_video_path(input_file_path, output_dir_path, slow_factor, output_fps_str)

    # If output video already exists, we can skip this
    if os.path.isfile(output_video_path):
        print(f"Video file already exists. Skipping: {output_video_path}")
        return
    
    # Make the output directory
    output_dir_path.mkdir(parents=True, exist_ok=True)

    # Make input frames directory
    input_frames_dir = output_dir_path / "input_frames"
    shutil.rmtree(input_frames_dir, ignore_errors=True)
    input_frames_dir.mkdir()
    print(f"Created directory for input frames: {input_frames_dir}")

    # Make output frames directory
    output_frames_dir = output_dir_path / "output_frames"
    shutil.rmtree(output_frames_dir, ignore_errors=True)
    output_frames_dir.mkdir()
    print(f"Created directory for output frames: {output_frames_dir}")

    # Use ffmpeg to extract input frames
    print("Extracting input frames...")
    os.system(f"ffmpeg -i '{input_file_path}' '{input_frames_dir}/%05d.png'")
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
    
    # Helpful logging
    print("********************************")
    print(f"* Processing {input_file_path.name}")
    print("********************************")

    # Interpolate with DAIN
    time_step = 1 / float(slow_factor)
    os.system(
        f" \
            python {dain_exec_path} \
            --netName DAIN \
            --time_step {time_step} \
            --start_frame 1 \
            --end_frame {num_input_frames} \
            --frame_input_dir '{input_frames_dir}' \
            --frame_output_dir '{output_frames_dir}' \
        "
    )

    # Calculate output fps
    input_fps_str = sp.getoutput(f"ffprobe -v 0 -of csv=p=0 -select_streams v:0 -show_entries stream=r_frame_rate {input_file_path}")
    input_fps_n, input_fps_d = [int(n) for n in input_fps_str.split("/")]
    
    output_fps_n = input_fps_n * slow_factor
    output_fps_d = input_fps_d

    if output_fps < 1:
        output_fps_str = f"{output_fps_n}/{input_fps_d}"
        output_fps_int = int(input_fps_n)
    else:
        output_fps_str = str(output_fps)
        output_fps_int = output_fps

    # Generate output video
    os.system(f"ffmpeg -y -r {output_fps_str} -f image2 -pattern_type glob -i '{output_frames_dir}/*.png' -pix_fmt yuv420p '{output_video_path}'")

    # Clean up
    shutil.rmtree(input_frames_dir, ignore_errors=True)
    shutil.rmtree(output_frames_dir, ignore_errors=True)

    print(f"Completed processing video: {output_video_path}")
