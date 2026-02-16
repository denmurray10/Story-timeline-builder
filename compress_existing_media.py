import os
import django
import sys

# Setup Django environment
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timeline_project.settings')
django.setup()

from timeline.models import Book, Character, WorldEntry
from timeline.utils.image_processing import compress_image
from django.core.files.uploadedfile import UploadedFile

def compress_existing_images():
    print("🚀 Starting bulk image compression for existing media...")

    # 1. Process Book Covers
    books = Book.objects.exclude(image='')
    print(f"📚 Found {books.count()} books with images.")
    for book in books:
        try:
            print(f"  - Compressing cover for: {book.title}...")
            # We pass the image field itself. 
            # compress_image returns a ContentFile.
            new_image = compress_image(book.image, target_type='book_cover')
            if new_image:
                # To avoid recursion in the model's save method which checks for UploadedFile (which ContentFile is not always),
                # we update the field and save. 
                # Note: our model save method checks isinstance(self.image.file, UploadedFile).
                # ContentFile won't trigger that check, preventing infinite loops.
                book.image.save(new_image.name, new_image, save=True)
                print(f"    ✅ Success: {new_image.name}")
        except Exception as e:
            print(f"    ❌ Error processing {book.title}: {e}")

    # 2. Process Character Profiles
    chars = Character.objects.exclude(profile_image='')
    print(f"\n👥 Found {chars.count()} characters with profile images.")
    for char in chars:
        try:
            print(f"  - Compressing profile for: {char.name}...")
            new_image = compress_image(char.profile_image, target_type='character_profile')
            if new_image:
                char.profile_image.save(new_image.name, new_image, save=True)
                print(f"    ✅ Success: {new_image.name}")
        except Exception as e:
            print(f"    ❌ Error processing {char.name}: {e}")

    # 3. Process World Entries
    entries = WorldEntry.objects.exclude(image='')
    print(f"\n🌍 Found {entries.count()} world entries with images.")
    for entry in entries:
        try:
            print(f"  - Compressing image for: {entry.title}...")
            new_image = compress_image(entry.image, target_type='world_image')
            if new_image:
                entry.image.save(new_image.name, new_image, save=True)
                print(f"    ✅ Success: {new_image.name}")
        except Exception as e:
            print(f"    ❌ Error processing {entry.title}: {e}")

    print("\n✨ Bulk compression complete!")

if __name__ == "__main__":
    compress_existing_images()
