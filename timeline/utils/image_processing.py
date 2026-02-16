import os
import io
from PIL import Image
from django.core.files.base import ContentFile

def compress_image(image_field, target_type='general', quality=85, format='WEBP'):
    """
    Compresses and resizes an image from a Django ImageField based on target_type.
    Returns a ContentFile ready to be saved back to the field.
    """
    if not image_field:
        return None

    # Configuration for different targets
    CONFIG = {
        'book_cover': (600, 900),
        'character_profile': (400, 400),
        'world_image': (1200, 800),
        'general': (800, 800)
    }
    
    size = CONFIG.get(target_type, CONFIG['general'])

    # Open the image using Pillow
    img = Image.open(image_field)
    
    # Handle transparency and formats
    if img.mode in ('RGBA', 'P') and format.upper() == 'JPEG':
        img = img.convert('RGB')
    elif img.mode != 'RGB' and format.upper() == 'WEBP':
        img = img.convert('RGBA')
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Resize while maintaining aspect ratio (Thumbnail)
    # However, for profile pics, we might want to crop to square?
    # User said "resize", let's stick to thumbnail for safety, or optional cropping.
    img.thumbnail(size, Image.Resampling.LANCZOS)

    # Save to a BytesIO object
    output = io.BytesIO()
    
    # Generate new filename
    original_filename = os.path.basename(image_field.name)
    name_without_ext = os.path.splitext(original_filename)[0]
    new_name = f"{name_without_ext}.{format.lower()}"
    
    img.save(output, format=format, quality=quality, optimize=True)
    output.seek(0)

    return ContentFile(output.read(), name=new_name)
