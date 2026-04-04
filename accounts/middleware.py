import jwt
import os
from django.contrib.auth import login
from .models import User
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)

class SupabaseAuthMiddleware(MiddlewareMixin):
    """
    Middleware to automatically authenticate Django users based on a Supabase JWT.
    This enables 'Daily Login' to be managed by Supabase Auth.
    """
    def process_request(self, request):
        # Skip if user is already authenticated via session
        if request.user.is_authenticated:
            return None

        # Look for the token in cookies or Authorization header
        token = request.COOKIES.get('sb-access-token')
        if not token:
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            return None

        try:
            # Verify the JWT using the Supabase JWT Secret (same as SERVICE_ROLE_KEY base)
            # Actually, Supabase uses the 'JWT Secret' found in Dashboard -> API settings.
            # Usually it is the same secret that signs the service_role key.
            # For this implementation, we assume it's provided in the environment.
            jwt_secret = os.environ.get('SUPABASE_JWT_SECRET') or os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
            
            if not jwt_secret:
                return None
                
            # Note: In production, you'd use a public key if it's asymmetric, 
            # but Supabase uses HS256 with a shared secret by default.
            payload = jwt.decode(token, jwt_secret, algorithms=["HS256"], options={"verify_aud": False})
            
            supabase_uid = payload.get('sub')
            if not supabase_uid:
                return None
                
            # Find the matching Django user
            try:
                user = User.objects.get(supabase_uid=supabase_uid)
                if user.is_active:
                    # Log the user into the Django session
                    login(request, user)
                    logger.info(f"Authenticated user {user.username} via Supabase JWT.")
            except User.DoesNotExist:
                logger.warning(f"Supabase UID {supabase_uid} found in token but no matching Django user exists.")
                
        except jwt.ExpiredSignatureError:
            logger.debug("Supabase JWT has expired.")
        except jwt.InvalidTokenError as e:
            logger.debug(f"Invalid Supabase JWT: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in SupabaseAuthMiddleware: {e}")

        return None
