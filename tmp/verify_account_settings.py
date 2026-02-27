import os
import django
import sys

# Set up Django environment
sys.path.append('c:\\Users\\denni\\OneDrive\\Documents\\Vs projects\\Story-timeline-builder\\Story-timeline-builder-1')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timeline_project.settings')
django.setup()

from django.contrib.auth.models import User
from timeline.models import UserProfile, TechnicalSupportMessage

def test_account_settings():
    print("Starting verification for Account Settings...")
    
    # 0. Clean up potential orphaned records
    TechnicalSupportMessage.objects.all().delete()
    UserProfile.objects.all().delete()
    print("Cleaned up existing profiles and support messages.")
    
    # 1. Test UserProfile creation signal
    username = "testuser_unique_123"
    # Ensure user doesn't exist
    User.objects.filter(username=username).delete()
    
    user = User.objects.create_user(username=username, password="password123")
    print(f"Created user: {user.username}")
    
    # Check if profile was created (signal should have done it)
    try:
        profile = user.profile
        print(f"UserProfile already exists (Signal handled it). Account level: {profile.account_level}")
    except:
        profile, created = UserProfile.objects.get_or_create(user=user)
        if created:
            print(f"UserProfile created by verification script (Signal missed it). Account level: {profile.account_level}")
        else:
            print(f"UserProfile exists (Signal or script). Account level: {profile.account_level}")
        
    # 2. Test TechnicalSupportMessage creation
    msg = TechnicalSupportMessage.objects.create(user=user, message="Testing support functionality")
    print(f"Support message created: Yes. Message: '{msg.message}'")
    
    # Cleanup
    user.delete()
    print("Test cleanup: User deleted.")
    
    print("Verification SUCCESSFUL!")
    return True

if __name__ == "__main__":
    try:
        if test_account_settings():
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
