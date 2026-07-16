import os

# Google returns the granted OAuth scopes reordered and adds "openid" (implied by
# userinfo.email), which makes oauthlib's strict equality check raise "Scope has changed" during
# the token exchange. The granted scopes are the same ones we requested, so relax the check to a
# warning. Set here (the email package init) so it's in effect before gmail.py runs a token
# exchange, regardless of import path.
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")
