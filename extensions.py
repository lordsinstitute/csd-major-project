"""Extension objects that are shared between app.py and the blueprints."""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Limits are attached to routes with decorators and activated in create_app().
# Storage and on/off switch come from the RATELIMIT_* config values.
limiter = Limiter(key_func=get_remote_address)