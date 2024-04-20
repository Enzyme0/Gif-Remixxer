import sys
import os
import shutil
import random
from multiprocessing import Pool
from PIL import Image
from wand.image import Image as WandImage

def gif_to_frames(gif_path):
    with Image.open(gif_path) as gif:
        num_frames = gif.n_frames
        os.makedirs("framestemp", exist_ok=True)
        frames = []
        for i in range(num_frames):
            gif.seek(i)
            frame_path = f"framestemp/frame_{i}.png"
            gif.save(frame_path)
            frames.append(frame_path)
    return frames

def process_frame(args):
    from wand.image import Image
    frame_path, remix_type, output_path, scale = args

    with Image(filename=frame_path) as img:
        if remix_type == "swirl":
            img.swirl(degree=180)
        elif remix_type == "size":
            img.resize(int(img.width * scale), int(img.height * scale))
        elif remix_type == "sepia":
            img.sepia_tone(threshold=0.8)
        elif remix_type == "invert":
            img.negate()
        elif remix_type == "edge":
            img.edge(radius=1)
        elif remix_type == "blur":
            img.gaussian_blur(radius=5, sigma=1.5)
        elif remix_type == "mirror":
            img.flop()
        elif remix_type == "deepfry":
            img.modulate(brightness=200, saturation=200, hue=100)
            img.contrast(sharpen=True)
            img.noise(noise_type='gaussian', attenuate=0.5)

        img.save(filename=output_path)
    return output_path

def create_gif(frames, output_path, original_gif_path):
    with Image.open(original_gif_path) as original:
        duration = original.info.get('duration', 100)  # Get the duration of the original GIF
        loop = original.info.get('loop', 0)            # Get the loop settings of the original GIF

    images = [Image.open(frame) for frame in frames]
    images[0].save(output_path, save_all=True, append_images=images[1:], duration=duration, loop=loop, optimize=True)
    # Clean up the PNG frames after creating the GIF
    for frame in frames:
        os.remove(frame)

def apply_effects_to_all_frames(frames, remix_types, output_folder, original_gif_path):
    base_name = os.path.splitext(os.path.basename(original_gif_path))[0]
    output_dir = os.path.join("gifs", base_name, output_folder)
    os.makedirs(output_dir, exist_ok=True)
    pool = Pool()
    results = []

    for remix_type in remix_types:
        frame_output_paths = [os.path.join(output_dir, f"{remix_type}_frame_{i}.png") for i, _ in enumerate(frames)]
        scale = random.uniform(1, 3) if remix_type == "random" else 2
        args = [(frame, remix_type, frame_output_path, scale) for frame, frame_output_path in zip(frames, frame_output_paths)]
        results.extend(pool.map(process_frame, args))

        # Create GIF from processed frames and then delete the temporary PNG files
        gif_output_path = os.path.join(output_dir, f"{remix_type}.gif")
        create_gif(frame_output_paths, gif_output_path, original_gif_path)

    pool.close()
    pool.join()

def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py <gif_path> <remix_type> [scale (if applicable)]")
        sys.exit(1)

    gif_path = sys.argv[1]
    remix_type = sys.argv[2]
    os.makedirs("gifs", exist_ok=True)  # Ensure the main output directory exists

    frames = gif_to_frames(gif_path)
    if remix_type == "salad" or remix_type == "random":
        remix_types = ["swirl", "size", "sepia", "invert", "edge", "blur", "mirror", "deepfry"]
        apply_effects_to_all_frames(frames, remix_types, remix_type, gif_path)
    else:
        apply_effects_to_all_frames(frames, [remix_type], "standard", gif_path)

    shutil.rmtree("framestemp")  # Cleanup temp frames directory after processing

if __name__ == "__main__":
    main()
