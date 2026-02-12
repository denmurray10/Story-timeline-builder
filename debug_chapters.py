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
    
    for user in users:
        print(f"\nUser: {user.username}")
        books = Book.objects.filter(user=user)
        print(f"  Books: {books.count()}")
        
        total_chapters = Chapter.objects.filter(book__user=user).count()
        completed_chapters = Chapter.objects.filter(book__user=user, is_complete=True).count()
        
        print(f"  Total Chapters: {total_chapters}")
        print(f"  Completed Chapters (is_complete=True): {completed_chapters}")
        
        # Check first few chapters to see their status
        chapters = Chapter.objects.filter(book__user=user)[:5]
        for ch in chapters:
            print(f"    - Chapter {ch.chapter_number}: is_complete={ch.is_complete}")

if __name__ == "__main__":
    check_chapters()
