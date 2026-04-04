from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from .supabase_utils import update_supabase_user_status
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def sync_user_approval_to_supabase(sender, instance, created, **kwargs):
    """
    Syncs the Django is_active status to Supabase Auth app_metadata.
    This allows Supabase RLS to check if the user is 'approved'.
    """
    # Only sync if the user has a linked Supabase UID
    if instance.supabase_uid:
        try:
            # We treat is_active as the 'approved' flag in Supabase
            update_supabase_user_status(instance.supabase_uid, instance.is_active)
            logger.info(f"Synced approval status for {instance.username} to Supabase: {instance.is_active}")
        except Exception as e:
            logger.error(f"Failed to sync approval status for {instance.username} to Supabase: {e}")
