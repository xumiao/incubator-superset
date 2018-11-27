from flask import g


def current_user():
    try:
        return g.user
    except Exception:
        return None
