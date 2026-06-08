import os
import math
import random
import numpy as np
from PIL import Image, ImageDraw

COLORS_RGB = {
    '可回收': (33, 150, 243),
    '厨余': (76, 175, 80),
    '有害': (244, 67, 54),
    '其他': (158, 158, 158)
}

PATTERNS = {
    '可回收': ['circle', 'rectangle', 'diamond', 'triangle', 'hexagon'],
    '厨余': ['oval', 'wave', 'blob', 'arc', 'spiral'],
    '有害': ['cross', 'star', 'bolt', 'skull', 'warning'],
    '其他': ['dots', 'grid', 'lines', 'mesh', 'crisscross']
}

random.seed(42)
np.random.seed(42)

def create_sample_image(class_name, index, output_dir):
    img_size = 224
    base_r, base_g, base_b = COLORS_RGB[class_name]
    
    bg_r = min(255, base_r + 80)
    bg_g = min(255, base_g + 80)
    bg_b = min(255, base_b + 80)
    
    img_array = np.zeros((img_size, img_size, 3), dtype=np.uint8)
    
    for c in range(3):
        noise = np.random.randint(-20, 20, (img_size, img_size), dtype=np.int16)
        base_val = [bg_r, bg_g, bg_b][c]
        channel = np.clip(base_val + noise, 0, 255).astype(np.uint8)
        img_array[:, :, c] = channel
    
    img = Image.fromarray(img_array)
    draw = ImageDraw.Draw(img)
    
    margin = 20
    draw.rectangle([margin, margin, img_size-margin, img_size-margin], 
                   outline=(base_r, base_g, base_b), width=4)
    
    inner_margin = 45
    inner_color = (min(255, base_r+40), min(255, base_g+40), min(255, base_b+40))
    draw.rectangle([inner_margin, inner_margin, img_size-inner_margin, img_size-inner_margin], 
                   fill=inner_color)
    
    pattern = PATTERNS[class_name][index % len(PATTERNS[class_name])]
    center = img_size // 2
    shape_color = (base_r, base_g, base_b)
    shape_size = 40 + (index % 3) * 10
    
    if pattern == 'circle':
        draw.ellipse([center-shape_size, center-shape_size, center+shape_size, center+shape_size], 
                     fill=shape_color)
    elif pattern == 'rectangle':
        draw.rectangle([center-shape_size, center-shape_size, center+shape_size, center+shape_size], 
                       fill=shape_color)
    elif pattern == 'diamond':
        points = [(center, center-shape_size), (center+shape_size, center), 
                  (center, center+shape_size), (center-shape_size, center)]
        draw.polygon(points, fill=shape_color)
    elif pattern == 'triangle':
        points = [(center, center-shape_size), (center+shape_size, center+shape_size), 
                  (center-shape_size, center+shape_size)]
        draw.polygon(points, fill=shape_color)
    elif pattern == 'hexagon':
        points = []
        for i in range(6):
            angle = math.pi / 3 * i - math.pi / 6
            px = center + shape_size * math.cos(angle)
            py = center + shape_size * math.sin(angle)
            points.append((px, py))
        draw.polygon(points, fill=shape_color)
    elif pattern == 'oval':
        draw.ellipse([center-shape_size*1.3, center-shape_size*0.7, 
                      center+shape_size*1.3, center+shape_size*0.7], fill=shape_color)
    elif pattern == 'wave':
        for dy in range(-2, 3):
            y_off = center + dy * 20
            for x in range(center-shape_size, center+shape_size, 2):
                y = y_off + int(10 * math.sin(x * 0.1))
                draw.ellipse([x-2, y-2, x+2, y+2], fill=shape_color)
    elif pattern == 'blob':
        for i in range(8):
            angle = math.pi * 2 / 8 * i
            bx = center + int(shape_size * 0.7 * math.cos(angle))
            by = center + int(shape_size * 0.7 * math.sin(angle))
            r = 15 + (index % 3) * 5
            draw.ellipse([bx-r, by-r, bx+r, by+r], fill=shape_color)
    elif pattern == 'arc':
        draw.arc([center-shape_size, center-shape_size, center+shape_size, center+shape_size], 
                 0, 300, fill=shape_color, width=8)
    elif pattern == 'spiral':
        for t in range(0, 360, 5):
            angle = math.radians(t)
            r = shape_size * t / 360
            x = center + int(r * math.cos(angle))
            y = center + int(r * math.sin(angle))
            draw.ellipse([x-3, y-3, x+3, y+3], fill=shape_color)
    elif pattern == 'cross':
        w = shape_size // 3
        draw.rectangle([center-w, center-shape_size, center+w, center+shape_size], fill=shape_color)
        draw.rectangle([center-shape_size, center-w, center+shape_size, center+w], fill=shape_color)
    elif pattern == 'star':
        points = []
        for i in range(10):
            angle = math.pi / 5 * i - math.pi / 2
            r = shape_size if i % 2 == 0 else shape_size * 0.4
            px = center + r * math.cos(angle)
            py = center + r * math.sin(angle)
            points.append((px, py))
        draw.polygon(points, fill=shape_color)
    elif pattern == 'bolt':
        points = [(center-5, center-shape_size), (center+shape_size//2, center-5), 
                  (center+5, center+5), (center+shape_size//2+10, center+5), 
                  (center-10, center+shape_size), (center-5, center+5), 
                  (center-shape_size//2, center+5)]
        draw.polygon(points, fill=shape_color)
    elif pattern == 'skull':
        draw.ellipse([center-shape_size, center-shape_size, center+shape_size, center+shape_size//2], 
                     fill=shape_color)
        draw.ellipse([center-10, center-10, center-2, center-2], fill=(255,255,255))
        draw.ellipse([center+2, center-10, center+10, center-2], fill=(255,255,255))
    elif pattern == 'warning':
        points = [(center, center-shape_size), (center+shape_size, center+shape_size), 
                  (center-shape_size, center+shape_size)]
        draw.polygon(points, fill=shape_color, outline=(0,0,0))
    elif pattern == 'dots':
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                x = center + dx * 18
                y = center + dy * 18
                draw.ellipse([x-5, y-5, x+5, y+5], fill=shape_color)
    elif pattern == 'grid':
        for i in range(5):
            pos = inner_margin + i * (img_size - 2 * inner_margin) // 4
            draw.line([(pos, inner_margin), (pos, img_size-inner_margin)], fill=shape_color, width=2)
            draw.line([(inner_margin, pos), (img_size-inner_margin, pos)], fill=shape_color, width=2)
    elif pattern == 'lines':
        for i in range(8):
            y = inner_margin + 15 + i * 18
            draw.line([(inner_margin+10, y), (img_size-inner_margin-10, y)], fill=shape_color, width=3)
    elif pattern == 'mesh':
        for i in range(0, img_size, 20):
            draw.line([(i, 0), (i+img_size, img_size)], fill=shape_color, width=1)
    elif pattern == 'crisscross':
        for i in range(0, img_size, 25):
            draw.line([(0, i), (img_size, i)], fill=shape_color, width=1)
            draw.line([(i, 0), (i, img_size)], fill=shape_color, width=1)
    
    variation = (index * 7) % 50 - 25
    img_array = np.array(img, dtype=np.int16)
    img_array = np.clip(img_array + variation, 0, 255).astype(np.uint8)
    img = Image.fromarray(img_array)
    
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{class_name}_{index+1}.jpg"
    filepath = os.path.join(output_dir, filename)
    img.save(filepath, 'JPEG', quality=95)
    print(f"已创建: {filepath}")

def generate_samples(num_per_class=8):
    base_dirs = ['data/train', 'data/valid']
    
    for base_dir in base_dirs:
        for class_name in COLORS_RGB.keys():
            class_dir = os.path.join(base_dir, class_name)
            num = num_per_class if base_dir == 'data/train' else max(2, num_per_class // 2)
            for i in range(num):
                create_sample_image(class_name, i, class_dir)

if __name__ == '__main__':
    print("开始生成示例图片...")
    generate_samples(num_per_class=8)
    print("示例图片生成完成!")
