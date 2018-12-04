from flask import g
import logging
logger = logging.getLogger(__name__)

# TODO: this unprotected context is currently for testing purpose
_user = None


def current_user():
    try:
        return _user or g.user
    except Exception:
        return None


def set_current_user(user):
    try:
        g.user = user
    except Exception:
        msg = 'Flask context does not allow setting the user, use unprotected context instead'
        logger.warning(msg)
        global _user
        _user = user
