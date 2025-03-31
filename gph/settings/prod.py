from .base import *

DEBUG = False

IS_TEST = False

# Used for constructing URLs; include the protocol and trailing
# slash (e.g. 'https://galacticpuzzlehunt.com/')
# DOMAIN = 'http://fduph24.sapium.site/'
# DOMAIN = 'http://localhost:8000/'
# FIXME 
DOMAIN = 'https://fduph24.fdupuzzle.fun/'

# STATIC_ROOT = '/static/'

# List of places you're serving from, e.g.
# ['galacticpuzzlehunt.com', 'gph.example.com']; or just ['*']
ALLOWED_HOSTS = [
  '127.0.0.1', 'localhost',
  'fduph24.sapium.site', 'sapium.site',
  'fduph24.fdupuzzle.fun', 'fdupuzzle.fun'
]
ALLOWED_HOSTS = ['*']

RECAPTCHA_SCORE_THRESHOLD = 0.0

# Google Analytics
GA_CODE = '''
<script>
  /* FIXME */
</script>
'''

HUNT_START_TIME = timezone.make_aware(datetime.datetime(
    year=2025,
    month=3,
    day=29,
    hour=20,
    minute=00,
), timezone=datetime.timezone(datetime.timedelta(hours=8)))
HUNT_END_TIME = timezone.make_aware(datetime.datetime(
    year=2025,
    month=4,
    day=8,
    hour=20,
    minute=00,
), timezone=datetime.timezone(datetime.timedelta(hours=8)))
HUNT_CLOSE_TIME = timezone.make_aware(datetime.datetime(
    year=2025,
    month=4,
    day=8,
    hour=20,
    minute=00,
), timezone=datetime.timezone(datetime.timedelta(hours=8)))
