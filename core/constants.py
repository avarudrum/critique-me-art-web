# Defining focus areas for art critiques.

FOCUS_AREAS = [
    ('composition', 'Composition'),
    ('color', 'Color'),
    ('technique', 'Technique'),
    ('concept', 'Concept'),
    ('perspective', 'Perspective'),
]

FOCUS_AREA_KEYS = [key for key, _ in FOCUS_AREAS]

# Cloudinary's free plan rejects uploads over 10 MB, so catch it in the form
# instead of letting the API call fail.
MAX_IMAGE_BYTES = 10 * 1024 * 1024