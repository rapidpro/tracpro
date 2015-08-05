#!yaml|gpg

environment: staging

# FIXME: Change to match staging domain name
domain: edutrac-staging.cakt.us

# FIXME: Update to the correct project repo
repo:
  url: git@github.com:caktus/edutrac.git
  branch: master

# Addtional public environment variables to set for the project
env:
  FOO: BAR

# Uncomment and update username/password to enable HTTP basic auth
# Password must be GPG encrypted.
http_auth:
  "caktus": |-
    -----BEGIN PGP MESSAGE-----
    Version: GnuPG v1.4.11 (GNU/Linux)

    hQEMA9NkrjRoSxYeAQgAzUVAWCci2twVwL81G8js9wW/n1ZqMGSt/MoMFWfpUTfY
    b6uC8yk45QKBy2MmFdqiN9jjNZtkjFZIADNx4qCw5mhq9yk+s7t2omvTo89xC5Vb
    F1Mo6byaHfAEVcD3nGNdvi6DWOe/FJsYGBDk8Q3dDx6iHBbz34KkeBxgWp3Fml1S
    lhBYiLd9Qv/IRXFs6Z4VjolQ0YaV01Hku4exRgmpQGK511efQepLrlnvGHdQwLJQ
    pHpm0hyBQpiMD/JY8G0pkNFqplzKColJEQyW3sYA8sgNgrIQvT/WxsQuyKjtBHJF
    Dg5O2jfhR/Y5UMzWR4zqGzFG1sT/aE5eLv++fJ4ILtJBAeF53eyuzdtxB0NM7l+a
    8Tywv33b9nXVP+sbyhFdB+DfclnaRw3M9HHjYjX0iBhGzQz/T6hpaLQIOjrzZrFz
    1wQ=
    =d4dU
    -----END PGP MESSAGE-----

# Private environment variables. Must be GPG encrypted.
secrets:
  "DB_PASSWORD": |-
    -----BEGIN PGP MESSAGE-----
    Version: GnuPG v1.4.11 (GNU/Linux)

    hQEMA9NkrjRoSxYeAQgAqYyeoiGJ9MOd1a/jBavISZtpA+qWz/iv6cUQhgOYADYc
    TQd5DIsBZc0VvuXR0vri+2Mw6I0qsFkGd4wqV1da+Lbj9FqZUdwNQ8Ij968EOA7O
    TvdSZ2veniIoJd9A2UyeBe887LSNqlWwXJinfVC6RWf7YAl8pdomY63u2ceKB4Hq
    A6/VMIHzYF3Lu4M10VTAmGfmFUBhtwpKBdN7Rr5u0gVHZvH1v0Dqp2VfRzmTiS50
    elEr9bLzYT3jyc77i37i3KDsuKev69fXFjtmTXWv5vM/41gi86SLqdv+HtDtTV7f
    6J0cT9AIQN9PQ/au/FDNZz2o0ez7g1Us0+ijirjE+NJHARaOu+PyVRr4V6AuoHxt
    rdtmY5sOAo0kPfjGc37Zh9YZT4orT9pG5NX9O8wRuXhiTx5z6WVM2lhomZ/i4UkU
    PiYJm8jQN2U=
    =Zfv/
    -----END PGP MESSAGE-----
  "SECRET_KEY": |-
    -----BEGIN PGP MESSAGE-----
    Version: GnuPG v1.4.11 (GNU/Linux)

    hQEMA9NkrjRoSxYeAQf+LT8yDLI9MuOqD8mzwDewRFd1iUN+GPY0A6jZ7AeQ78Ic
    Lu8hIT2f9J2LZms+tyspZDUX0z2u8cyogeQLcNnXrogEYnYBe/AuT7PoQdndpF5V
    npHgBTfshXzLNHNu3gjpZfCbnG4BOaDt6wl6Exv7d7quybPr19i2TTDU4d6iEyHR
    GutXqwwWuqImegxXNUUtOOiIFah9yg98GvMdpL2xsc0e9m2tC94GGwev+DxZGubk
    VOxBSYDPlggm4Nrvs7RKBB04oVOrgCvJdYAUDo6MiUVRTr7SRn9D5t3xNuMhx1Re
    3/IkQ8U+hN2ukimHICj3SBFX7rqBEbKTJknO5mdL8dJ7ASzJVT37K4XtTQekRy5Q
    4FIz2p+aESsb0GAcQH/3QsJ68I4LsElZVkz+/TKyjWICDcO6BQRDfN8rRBqDJVCR
    ZWr2f+eEMhaWmjsvmWRWUPTvYDAmoOtGhFcFWotQCNZUB7BmJ0spQpFvrEF2Rug3
    xMF8i4+f2S1UZxKf
    =y21C
    -----END PGP MESSAGE-----
  "BROKER_PASSWORD": |-
    -----BEGIN PGP MESSAGE-----
    Version: GnuPG v1.4.11 (GNU/Linux)

    hQEMA9NkrjRoSxYeAQf8CfhzCs88GmUK+UivznT0M2kvujmOSSnajzohrOKqF5O4
    A4uyfZm3LlcK9z4BaOYKDQTTHSjWtu3bySNN33EGUwJi7DBGo5wDyE1he1L6aT50
    AJA+nEHV8wgI37xrfthUFcBDTsn3tz2/+FBndh5n7F+f4FQy4iKIWhIuT8FQWlFp
    YlqCrHG9Leh9aGIwsuZteM9/5qzDdXFk8GRf7mXONjUOOa194kz/1j42OA2Dbcdw
    BNALORstG6j9vHbeRwz6XgUPp+ILlrWjkfzzA9++x3D3NIKUkf+sd2hWwt1iju4p
    8JI8C12PXrLpnRbP2yHZoFbDxHP90v1IqJT9PlUb6dJJARCanl+uc07cVpX9FsPY
    5JSdztVoLKPWVAu2qj1RDlxCTj/bEgZ+UZGeU/Hn9w1+BDVTAm2qnSk7giUFbake
    3pJatTcwtXGtKQ==
    =N1GF
    -----END PGP MESSAGE-----

# Private deploy key. Must be GPG encrypted.
github_deploy_key: |-
  -----BEGIN PGP MESSAGE-----
  Version: GnuPG v1.4.11 (GNU/Linux)

  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
  =QgYn
  -----END PGP MESSAGE-----
  
# Uncomment and update ssl_key and ssl_cert to enabled signed SSL
# Must be GPG encrypted.
# {% if 'balancer' in grains['roles'] %}
# ssl_key: |
# -----BEGIN PGP MESSAGE-----
# -----END PGP MESSAGE-----
#
# ssl_cert: |
# -----BEGIN PGP MESSAGE-----
# -----END PGP MESSAGE-----
# {% endif %}
