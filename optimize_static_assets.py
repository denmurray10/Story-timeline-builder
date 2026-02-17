import os
from PIL import Image

def optimize_static_images():
    static_dir = r"c:\Users\denni\OneDrive\Documents\Vs projects\Story-timeline-builder\Story-timeline-builder-1\static\img"
    
    # Define portrait size
    PORTRAIT_SIZE = (800, 800)
    
    images_to_process = [
        # (filename, target_size, target_format)
        ('Elena.png', (400, 400), 'WEBP'),
        ('logo.png', (None, 256), 'WEBP'), 
        ('hero_mockup.png', (1600, None), 'WEBP'),
        ('relationship_map_figma.png', (1600, None), 'WEBP'),
        # Character Portraits - many are 8MB+ PNGs
        ('Agnes.png', PORTRAIT_SIZE, 'WEBP'),
        ('Lucius-Temple.png', PORTRAIT_SIZE, 'WEBP'),
        ('aunt-theodora.png', PORTRAIT_SIZE, 'WEBP'),
        ('Elise-temple.png', PORTRAIT_SIZE, 'WEBP'),
        ('Amy-temple.png', PORTRAIT_SIZE, 'WEBP'),
        ('Mrs.Temple.png', PORTRAIT_SIZE, 'WEBP'),
        ('Dora-new.png', PORTRAIT_SIZE, 'WEBP'),
        ('Agnes_alt.png', PORTRAIT_SIZE, 'WEBP'),
    ]

    print("🚀 Optimizing static assets...")

    for filename, size, fmt in images_to_process:
        input_path = os.path.join(static_dir, filename)
        output_filename = os.path.splitext(filename)[0] + f".{fmt.lower()}"
        output_path = os.path.join(static_dir, output_filename)

        if not os.path.exists(input_path):
            print(f"  ⚠️ Skipping {filename}: File not found.")
            continue

        try:
            with Image.open(input_path) as img:
                # Calculate size maintaining aspect ratio
                if size:
                    w, h = img.size
                    target_w, target_h = size
                    
                    if target_w and not target_h:
                        target_h = int((target_w / w) * h)
                    elif target_h and not target_w:
                        target_w = int((target_h / h) * w)
                    
                    # For portraits, we use thumbnail to maintain aspect but fit in the size
                    if target_w < w or target_h < h:
                        img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
                        print(f"  ✅ Resized {filename} to {img.width}x{img.height}")

                # Convert to RGB (standard) or keep RGBA if needed
                # WebP supports Alpha, so let's keep it if original has it
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
                
                img.save(output_path, format=fmt, quality=80, method=6)
                original_size = os.path.getsize(input_path) / 1024
                new_size = os.path.getsize(output_path) / 1024
                print(f"  ✨ Optimized {filename} -> {output_filename}")
                print(f"     {original_size:.1f}KB -> {new_size:.1f}KB ({(1 - new_size/original_size)*100:.1f}% saved)")

        except Exception as e:
            print(f"  ❌ Error optimizing {filename}: {e}")

if __name__ == "__main__":
    optimize_static_images()
