def get_session_config(env):
    return {
        "COOKIE_AGE": env("SESSION_COOKIE_AGE"),
        "INACTIVITY_TIMEOUT": env("SESSION_INACTIVITY_TIMEOUT"),
    }