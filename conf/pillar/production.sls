#!yaml|gpg

environment: production

domain: edutrac.io
repo:
  url: git@github.com:rapidpro/tracpro.git
  branch: master

# Additional public environment variables to set for the project
env:
  CSRF_COOKIE_DOMAIN: ".edutrac.io"
  HOSTNAME: "edutrac.io"
  SESSION_COOKIE_DOMAIN: ".edutrac.io"
  SITE_HOST_PATTERN: "https://%s.edutrac.io"

# Uncomment and update username/password to enable HTTP basic auth
# Password must be GPG encrypted.
# http_auth:
#   username: |-
#    -----BEGIN PGP MESSAGE-----
#    -----END PGP MESSAGE-----

# Private environment variables.
# Must be GPG encrypted.
# secrets:
#   "DB_PASSWORD": |-
#     -----BEGIN PGP MESSAGE-----
#     -----END PGP MESSAGE-----
#   "SECRET_KEY": |-
#     -----BEGIN PGP MESSAGE-----
#     -----END PGP MESSAGE-----

# Private deploy key. Must be GPG encrypted.
# github_deploy_key: |-
#    -----BEGIN PGP MESSAGE-----
#    -----END PGP MESSAGE-----

# Uncomment and update ssl_key and ssl_cert to enabled signed SSL/
# Must be GPG encrypted.
# {% if 'balancer' in grains['roles'] %}
# ssl_key: |-
#    -----BEGIN PGP MESSAGE-----
#    -----END PGP MESSAGE-----
#
# ssl_cert: |-
#    -----BEGIN PGP MESSAGE-----
#    -----END PGP MESSAGE-----
# {% endif %}
