"""
One-time helper: registers the 6 azkar/dua images already bundled in
media/mindfulness/ as real MindfulnessContent rows with the right phase,
so they show up immediately without manually re-uploading them in the admin.

Run once with: python manage.py seed_mindfulness
Safe to run again — it skips images that are already registered.
"""
from django.core.files import File
from django.core.management.base import BaseCommand
from apps.core.models import MindfulnessContent

SEED_ITEMS = [
    ('before_study_bird_understanding.png', MindfulnessContent.Phase.BEFORE_STUDY, 'Dua for understanding'),
    ('after_study_rose.png', MindfulnessContent.Phase.AFTER_STUDY, 'Dua for entrusting knowledge'),
    ('after_study_book.png', MindfulnessContent.Phase.AFTER_STUDY, 'Dua for finishing study'),
    ('azkar_stone_tasbih.png', MindfulnessContent.Phase.DURING_BREAK, 'Tasbih'),
    ('azkar_duck_reliance.png', MindfulnessContent.Phase.DURING_BREAK, 'Dua for reliance on Allah'),
    ('azkar_leaves_general.png', MindfulnessContent.Phase.DURING_BREAK, 'General adhkar'),
]


class Command(BaseCommand):
    help = 'Seeds the bundled azkar/dua images into MindfulnessContent (safe to re-run).'

    def handle(self, *args, **options):
        from django.conf import settings

        media_dir = settings.MEDIA_ROOT / 'mindfulness'
        created_count = 0

        for filename, phase, source in SEED_ITEMS:
            if MindfulnessContent.objects.filter(source=source).exists():
                self.stdout.write(f'Skipping {filename} (already registered)')
                continue

            file_path = media_dir / filename
            if not file_path.exists():
                self.stdout.write(self.style.WARNING(f'Missing file: {file_path}'))
                continue

            with open(file_path, 'rb') as f:
                item = MindfulnessContent(phase=phase, source=source, text='')
                item.image.save(filename, File(f), save=True)
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'Registered {filename} as {phase}'))

        self.stdout.write(self.style.SUCCESS(f'Done — {created_count} new item(s) registered.'))
