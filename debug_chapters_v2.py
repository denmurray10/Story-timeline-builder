import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timeline_project.settings')
django.setup()

from timeline.models import Chapter, Book, User

def check_chapters():
    users = User.objects.all()
    print(f"Total Users: {users.count()}")
    
    with open('chapter_debug.txt', 'w') as f:
        for user in users:
            f.write(f"\nUser: {user.username} (ID: {user.id}) | First Name: '{user.first_name}'\n")
            books = Book.objects.filter(user=user)
            f.write(f"  Books: {books.count()}\n")
            for b in books:
                 f.write(f"    - Book: '{b.title}' (ID: {b.id})\n")
            
            chapters = Chapter.objects.filter(book__user=user)
            f.write(f"  Total Chapters: {chapters.count()}\n")
            
            completed = chapters.filter(is_complete=True).count()
            f.write(f"  Chapters with is_complete=True: {completed}\n")
            
            with_content = chapters.exclude(content='').count()
            f.write(f"  Chapters with content: {with_content}\n")
            
            # List details of all chapters
            for ch in chapters:
                f.write(f"    - Ch {ch.chapter_number} '{ch.title}': is_complete={ch.is_complete}, word_count={ch.word_count}, content_len={len(ch.content)}\n")

    print("Debug info written to chapter_debug.txt")

if __name__ == "__main__":
    check_chapters()
