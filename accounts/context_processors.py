from .models import Profile

def profile(request):
    """Add `profile` to the template context when the user is authenticated."""
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            profile = None
        return {'profile': profile}
    return {'profile': None}
