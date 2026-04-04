import os
from supabase import create_client, Client
from django.conf import settings

def get_supabase_admin_client() -> Client:
    """
    Returns a Supabase client authenticated with the SERVICE_ROLE_KEY.
    Used for administrative actions like creating users and updating app_metadata.
    """
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment.")
        
    return create_client(url, key)

def create_supabase_user_admin(email, password, metadata=None):
    """
    Creates a user in Supabase Auth using the Admin API.
    """
    supabase = get_supabase_admin_client()
    # Note: Using the admin API to create the user immediately
    response = supabase.auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True, # Auto-confirm for system-created users
        "user_metadata": metadata or {}
    })
    return response

def update_supabase_user_status(supabase_uid, approved: bool):
    """
    Updates the app_metadata in Supabase Auth to reflect approval status.
    """
    supabase = get_supabase_admin_client()
    response = supabase.auth.admin.update_user_by_id(
        str(supabase_uid),
        {
            "app_metadata": {
                "approved": approved
            }
        }
    )
    return response
