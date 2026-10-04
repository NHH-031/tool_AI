import os
import sys
import time
from pathlib import Path
import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
from PIL import Image
import cv2
import numpy as np

def generate_local_option4():
    output_dir = Path("d:/Tool/output/option4_trial")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    model_id = "runwayml/stable-diffusion-v1-5"
    print(f"Loading local model: {model_id} on GPU RTX 3050...")
    start_load = time.time()
    
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        safety_checker=None
    )
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.enable_attention_slicing()
    pipe = pipe.to("cuda")
    print(f"Model loaded in {time.time() - start_load:.2f}s")
    
    prompt = (
        "minimalist black ink line art comic doodle, astronaut standing next to a landing spacecraft ladder on the surface of mars, "
        "notion style illustration, clean thick black contours, pure plain white background, simple vector line drawing, coloring book page"
    )
    negative_prompt = (
        "color, shading, gray tones, gradients, shadows, pencil smudge, noise, 3d, realistic photo, blurry, dirty background, watermark, text"
    )
    
    print("Generating image with prompt...")
    gen_start = time.time()
    generator = torch.Generator("cuda").manual_seed(42)
    
    image = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=25,
        guidance_scale=8.0,
        width=512,
        height=512,
        generator=generator
    ).images[0]
    
    print(f"Generated 512x512 in {time.time() - gen_start:.2f}s")
    
    raw_path = output_dir / "option4_raw_512.png"
    image.save(raw_path)
    print(f"Saved raw image to {raw_path}")
    
    # Post-process: Upscale to 1920x1080 and Clean noise/threshold to warm cream background
    print("Cleaning noise and upscaling to 1920x1080 for whiteboard engine...")
    img_np = np.array(image)
    if len(img_np.shape) == 3:
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_np
        
    # High-contrast line art thresholding
    # Keep crisp dark lines, map light gray noise to pure background
    _, thresh = cv2.threshold(gray, 210, 255, cv2.THRESH_BINARY)
    
    # Upscale cleanly with bicubic / nearest
    resized_thresh = cv2.resize(thresh, (1920, 1080), interpolation=cv2.INTER_CUBIC)
    _, final_mask = cv2.threshold(resized_thresh, 200, 255, cv2.THRESH_BINARY)
    
    # Re-apply warm cream background #F5EBD7 (BGR: 215, 235, 245) and dark ink #1A1A1A
    h, w = 1080, 1920
    canvas = np.zeros((h, w, 3), dtype=np.uint8)
    canvas[:] = (215, 235, 245) # Cream background
    
    ink_color = (26, 26, 26) # #1A1A1A
    canvas[final_mask < 128] = ink_color
    
    clean_path = output_dir / "option4_astronaut_cleaned_1080p.png"
    cv2.imwrite(str(clean_path), canvas)
    print(f"Saved cleaned 1080p artwork to {clean_path}")
    
    return str(raw_path), str(clean_path)

if __name__ == "__main__":
    generate_local_option4()
