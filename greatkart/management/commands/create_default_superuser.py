from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a default superuser if none exists'

    def handle(self, *args, **options):
        try:
            if not User.objects.filter(username='admin').exists():
                User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
                self.stdout.write(self.style.SUCCESS('Superuser created: admin / admin123'))
            else:
                self.stdout.write('Superuser already exists')
        except Exception as e:
            self.stderr.write(f'Error creating superuser: {str(e)}')
