import os
import sys
import django
import secrets
import string

# Add project root to sys.path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tbptld.settings')
django.setup()

from accounts.models import User
from accounts.supabase_utils import create_supabase_user_admin, update_supabase_user_status

def sync_existing_users():
    """
    One-time script to sync existing Django users to Supabase Auth.
    Generates a random password for users who don't have a Supabase account yet.
    """
    users_to_sync = User.objects.filter(supabase_uid__isnull=True)
    count = users_to_sync.count()
    print(f"Found {count} users to sync.")
    
    for user in users_to_sync:
        # Generate a random password for Supabase (since we don't know the Django hash)
        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        
        try:
            print(f"Syncing {user.username} ({user.email})...")
            # Create in Supabase
            sb_user = create_supabase_user_admin(
                user.email, 
                temp_password, 
                {"role": user.role, "username": user.username}
            )
            
            # Save the UID
            user.supabase_uid = sb_user.user.id
            user.save()
            
            # Sync the approval status
            update_supabase_user_status(user.supabase_uid, user.is_active)
            
            print(f"  Successfully synced {user.username}. Generated UID: {user.supabase_uid}")
            
        except Exception as e:
            print(f"  Failed to sync {user.username}: {e}")

if __name__ == "__main__":
    sync_existing_users()
