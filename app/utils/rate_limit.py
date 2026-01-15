import time
from app.utils.permissions import is_admin

RATE_LIMIT_SECONDS = 20

_last_request = {}


async def check_rate_limit(update, context):
    user = update.effective_user
    if not user:
        return True, None

    if await is_admin(update, context):
        return True, None

    now = time.time()
    last_time = _last_request.get(user.id)

    if last_time and now - last_time < RATE_LIMIT_SECONDS:
        remaining = int(RATE_LIMIT_SECONDS - (now - last_time))
        return False, remaining

    _last_request[user.id] = now
    return True, None
