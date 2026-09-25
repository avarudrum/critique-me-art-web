import os
import random
import cloudinary.uploader

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from artworks.models import Artwork, Tag, CritiqueRequest
from critiques.models import Critique, CritiqueSection
from core.constants import FOCUS_AREA_KEYS

User = get_user_model()

SEED_IMAGE_DIR = 'seed_images'

USERS = [
    ('gracie_m', 'gracie@example.com', 'Acrylic painter with a focus on portraiture.', 'acrylic paint'),
    ('haley_s', 'haley_s@example.com', 'Graphite and Charcoal artist working on contrast.', 'charcoal'),
    ('sana_k', 'sana@example.com', 'Digital abstract artist exploring texture.', 'digital'),
    ('terry_lb', 'terry@example.com', 'Beginner 3D sculptor.', '3D modeling'),
]

TAGS = [
    ('acrylic paint', 'medium'),
    ('digital', 'medium'),
    ('watercolour', 'medium'),
    ('charcoal', 'medium'),
    ('mixed-media', 'medium'),
    ('graphite', 'medium'),
    ('oil pastel', 'medium'),
    ('linework', 'technique'),
    ('contrast', 'technique'),
    ('mark-making', 'technique'),
    ('light and shadow', 'technique'),
    ('portrait', 'subject'),
    ('landscape', 'subject'),
    ('still-life', 'subject'),
    ('abstract', 'subject'),
    ('character art', 'subject'),
    ('sketch', 'subject'),
    ('Impressionism', 'subject'),
]

ARTWORKS = [
    {
        'title': 'Busking',
        'image': 'mix-media_1.jpg',
        'description': 'Acrylic mixed-media portrait, with oil pastel highlights.',
        'tags': ['mixed-media', 'still-life'],
        'focus_areas': ['composition'],
        'artist_note': "I am finding that the composition is a little flat. Should the shadows be deepened?",
    },
    {
        'title': 'all at once',
        'image': 'acrylic1.JPG',
        'description': 'Portrait study, playing with colour and texture.',
        'tags': ['acrylic paint', 'portrait'],
        'focus_areas': ['color', 'composition'],
        'artist_note': 'How could I push the background to feel more like a space rather than flat colours?',
    },
    {
        'title': 'Funky Colours',
        'image': 'Funky_colours.png',
        'description': 'Digital abstract space.',
        'tags': ['digital', 'linework', 'abstract'],
        'focus_areas': ['technique'],
        'artist_note': "Anyone have any tips for interesting linework in digital? I feel like it's a bit too flat.",
    },
    {
        'title': 'Light and shadow study',
        'image': 'charcoal_still.jpg',
        'description': 'From life, studio still-life with graphite and charcoal. Trying to push the contrast.',
        'tags': ['charcoal', 'light and shadow', 'still-life'],
        'focus_areas': ['technique'],
        'artist_note': 'How can I push the contrast even more with the charcoal? This is as dark as I can get it without losing the texture of the paper.',
    },
    {
        'title': 'Link sketch',
        'image': 'link_sketch.jpeg',
        'description': 'Graphite sketch of Link from Legend of Zelda.',
        'tags': ['graphite', 'character art', 'sketch'],
        'focus_areas': ['concept'],
        'artist_note': 'I am trying to develop a more stylized approach to my character art. Any tips on how to push this further?',
    },
    {
        'title': 'aging',
        'image': 'oilpastel.jpeg',
        'description': 'Concept oil pastel portrait, playing with texture and mark-making.',
        'tags': ['oil pastel', 'portrait', 'mark-making', 'Impressionism'],
        'focus_areas': ['technique', 'composition'],
        'artist_note': 'I am trying to incorporate Impressionism into this piece. How do I make the mark-making feel more intentional and less messy?',
    },
    {
        'title': 'Reaching out',
        'image': 'charcoal_hand.jpeg',        
        'description': 'Graphite and charcoal technique play. Trying to push the contrast and composition.',
        'tags': ['graphite', 'charcoal', 'still-life'],
        'focus_areas': ['composition', 'concept', 'technique'],
        'artist_note': 'I feel like I have improved my technique since my last piece, but backgrounds are my weak point. How do you guys make interesting backgrounds that don\'t distract from the subject, but also feel intentional?',
    },
]

CRITIQUE_BODIES = {
    # Each artwork maps to a list of critiques, one per critic.
    # Each critique maps a focus area to that critic's written feedback.
    # Add another {...} block to a list to give that piece a second critic.
    'Busking': [
        {
            'composition': "The composition is balanced and the subject is clearly the focus of the piece. That said, you're right that it reads flat. The shadow side of the figure is close in value to the background, so there's nothing separating the two. Deepening just the contact shadow where the figure meets the ground would do more than deepening the shadow overall.",
        },
    ],
    'all at once': [
        {
            'color': "Skin tones hold a nice range without going muddy on the shadow side. The background is a little flat because the colors are all at a similar saturation. Pushing the saturation down on the shapes furthest back would help them recede and give the piece more depth.",
            'composition': "The differing textures and lighting choices around the piece create a soft, almost angelic quality. Where it could go further is the background. Right now nothing in it varies in size or placement, so there's no sense of depth for the color to work with. A few shapes closer together and a few spread further apart would give the eye something to read as near and far before color even comes into it.",
        },
    ],
    'Funky Colours': [
        {
            'technique': "The colours and movement throughout the piece are clearly intentional, making it pleasing to the eyes. The flatness in the linework is likely because the stroke weight and opacity stay constant everywhere. Try varying the width and letting some lines break or fade rather than closing every shape completely. That's usually what separates flat digital linework from linework that has energy.",
        },
    ],
    'Light and shadow study': [
        {
            'technique': "The transition from the darkest point to the midtones stays visible instead of collapsing into flat black, which takes real control in charcoal. You're probably right that you're near the ceiling of how dark this area can go on this paper. Rather than pushing the same shadow darker, try adding one smaller, sharper dark accent nearby, like a cast shadow or a crevice. The existing dark will read as darker by comparison without you having to fight the paper.",
        },
    ],
    'Link sketch': [
        {
            'concept': "The expression carries Link's attitude without relying on any specific reference, which is a good sign of stylization. The proportions are staying close to a realistic reference, though, which is working against the stylization you're after. Stylizing usually means picking one or two features, the eyes, the silhouette, the limb proportions, and pushing those further than everywhere else, rather than adjusting the whole figure evenly.",
        },
    ],
    'aging': [
        {
            'technique': "The Impressionist quality you're going for is clearly coming through in the piece. The messiness you're noticing is likely because the mark direction isn't following the form underneath. Impressionist mark-making still tracks the structure, marks curve with the cheek, follow the jawline, and so on, they're just not blended. If the strokes follow the form even loosely, the same looseness will read as confident instead of messy.",
            'composition': "The colours and sketchy child-like quality tell the story in the piece very clearly. You could probably trim your piece around the edges, as they don't add to the piece and kind of look unfinished.",
        },
    ],
    'Reaching out': [
        {
            'composition': "The hand placement creates a clear line of action that the rest of the figure follows. For the background, a few soft, loose value shapes with no hard edges would give it presence without competing with the figure. Try to get that midtone throughout the piece to push the background back, while still keeping the movement you have created.",
            'concept': "The gesture reads as reaching toward something rather than just an arm position, making it interesting to look at compared to most figure studies. If you wanted to push the concept further beyond just a study you totally could. Interesting text could be fun, or even adding some colour into the piece if you're into that.",
            'technique': "The details are great in this piece. I love how you can see the hair on the arm! If you're going for a realism vibe, you're doing great and could just push the shadows further. If you're looking to stylize the piece, adding some purposeful marks throughout the hand that you used in the background could be interesting.",
        },
    ],
}

class Command(BaseCommand):
    help = 'Seed the database with sample users, artworks, and critiques.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete existing seeded data before creating new records.',
        )

    def handle(self, *args, **options):
        if not os.path.isdir(SEED_IMAGE_DIR):
            self.stderr.write(
                self.style.ERROR(
                    f"No '{SEED_IMAGE_DIR}/' folder found. "
                    "Create it, add your image files, and run this again."
                )
            )
            return

        if options['flush']:
            self.flush()

        with transaction.atomic():
            users = self.create_users()
            tags = self.create_tags()
            artworks = self.create_artworks(users, tags)
            count = self.create_critiques(users, artworks)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(users)} users, {len(artworks)} artworks, {count} critiques."
        ))
        self.stdout.write("All seeded accounts use the password: seedpass123")

    def flush(self):
        usernames = [u[0] for u in USERS]
        deleted, _ = User.objects.filter(username__in=usernames).delete()
        self.stdout.write(f"Flushed {deleted} seeded records.")

    def create_users(self):
        users = []
        for username, email, bio, medium in USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'bio': bio,
                    'primary_medium': medium,
                },
            )
            if created:
                user.set_password('seedpass123')
                user.save()
            users.append(user)
        return users

    def create_tags(self):
        tags = {}
        for name, category in TAGS:
            tag, _ = Tag.objects.get_or_create(
                name=name,
                defaults={'category': category},
            )
            tags[name] = tag
        return tags

    def create_artworks(self, users, tags):
        created = []
        for index, data in enumerate(ARTWORKS):
            if Artwork.objects.filter(title=data['title']).exists():
                continue

            artist = users[index % len(users)]

            image_path = os.path.join(SEED_IMAGE_DIR, data['image'])
            if not os.path.exists(image_path):
                self.stderr.write(self.style.WARNING(
                    f"  skipped {data['title']}: {data['image']} not found"
                ))
                continue

            upload_result = cloudinary.uploader.upload(image_path)

            artwork = Artwork(
                user=artist,
                title=data['title'],
                description=data['description'],
                image=upload_result['public_id'],
            )
            artwork.save()

            # Medium comes from these tags now, so every entry needs at least one
            # with category 'medium' -- the upload form enforces the same rule.
            artwork.tags.set(tags[name] for name in data['tags'])

            CritiqueRequest.objects.create(
                artwork=artwork,
                focus_areas=data['focus_areas'],
                artist_note=data['artist_note'],
            )

            created.append(artwork)
            self.stdout.write(f"  created {artwork.title}")

        return created

    def create_critiques(self, users, artworks):
        count = 0
        for artwork in artworks:
            written = CRITIQUE_BODIES.get(artwork.title, [])
            critics = [u for u in users if u != artwork.user]
            random.shuffle(critics)

            # zip pairs each written critique with a different critic,
            # and stops when either list runs out.
            for critic, sections in zip(critics, written):
                if Critique.objects.filter(artwork=artwork, user=critic).exists():
                    continue

                critique = Critique.objects.create(
                    artwork=artwork,
                    user=critic,
                )

                for category in artwork.critique_request.focus_areas:
                    if category not in FOCUS_AREA_KEYS:
                        continue
                    body = sections.get(category)
                    if not body:
                        continue
                    CritiqueSection.objects.create(
                        critique=critique,
                        category=category,
                        body=body,
                    )

                count += 1

        return count