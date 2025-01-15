import subprocess
import os

# Define the directory containing the images and the audio file
image_dir = 'local_media'  # Ensure this is the correct directory
audio_file = 'local_media\output_audio_1.mp3'
output_video_path = 'output_video/slideshow_video.mp4'

# Check if the image directory and audio file exist
if not os.path.exists(image_dir):
    raise FileNotFoundError(f"Image directory '{image_dir}' not found.")
if not os.path.exists(audio_file):
    raise FileNotFoundError(f"Audio file '{audio_file}' not found.")

# Create the output directory if it doesn't exist
os.makedirs('output_video', exist_ok=True)

# Generate a text file with the list of images and their durations
image_list_path = 'image_list.txt'
with open(image_list_path, 'w') as f:
    for image_file in sorted(os.listdir(image_dir)):
        if image_file.endswith(('.jpg', '.jpeg', '.png')):
            image_path = os.path.normpath(os.path.join(image_dir, image_file))
            f.write(f"file '{image_path.replace(os.sep, '/')}'\n")
            f.write("duration 4.5\n")  # Set each image duration to 2 seconds

# Add the last image without a duration to avoid FFmpeg errors
if os.path.exists(image_list_path):
    with open(image_list_path, 'a') as f:
        last_image = sorted(os.listdir(image_dir))[-1]
        last_image_path = os.path.normpath(os.path.join(image_dir, last_image))
        f.write(f"file '{last_image_path.replace(os.sep, '/')}'\n")

# Construct the FFmpeg command to create the video
command = [
    'ffmpeg',
    '-y',
    '-f', 'concat',
    '-safe', '0',
    '-i', image_list_path,
    '-i', audio_file,
    '-c:v', 'libx264',
    '-tune', 'stillimage',
    '-c:a', 'copy',  # Copy the audio without re-encoding
    '-pix_fmt', 'yuv420p',
    '-t', '21',  # Explicitly set video duration to match audio (15 seconds)
    output_video_path
]

print(f"Running FFmpeg command: {' '.join(command)}")

# Execute the command
result = subprocess.run(command, capture_output=True, text=True)

# Output FFmpeg logs if the process fails
if result.returncode != 0:
    print("FFmpeg Error:")
    print(result.stderr)
else:
    print(f"Slideshow video with audio created successfully at {output_video_path}")

# Clean up the temporary image list file
os.remove(image_list_path)
