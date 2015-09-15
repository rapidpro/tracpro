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
http_auth:
  "tracpro": |-
    -----BEGIN PGP MESSAGE-----
    Version: GnuPG v1.4.11 (GNU/Linux)

    hQEMAzBv9PsbguWNAQgAmavQ2p9r3YXp65y2PoGxHERa6UQGlWA9j66bQbSQ3tBu
    l/4PChFOW1ITb65BdThRZcwhP450h5rln24AWPLhSNGNbjdE/7ITWUSJUl55R+4v
    tuq07YyylfopOh95ijuVnqEXCxZ0XwBIasSsMuK/sKkO3ByoYCKTxVdw6yzQR/aZ
    wW6oF/d3BwdQoPeUzEI4O6eHPm7iSar9GCvh05O+CUZpgEwDydFb5KITzw/Xb0nh
    KjB9R85t5i21ilPjSwoiucZWXWAq6krUnihJAsLNA9TiATbDizJNjzR+Sdn9SAgU
    0zRzRvUrR4mBR7RMXzlFfXQbL4fGnNhzjcj2LztGZtJBAeuycSfSwzajx1xmFaR5
    90edvH8hLgv3zlHQIvotJOZ8+pVUauuSzvXkdbl0LeChf9X79xBl0gXIouhP/Wde
    bWY=
    =Rp7z
    -----END PGP MESSAGE-----

# Private environment variables.
# Must be GPG encrypted.
secrets:
  "DB_PASSWORD": |-
    -----BEGIN PGP MESSAGE-----
    Version: GnuPG v1.4.11 (GNU/Linux)

    hQEMAzBv9PsbguWNAQf+O2oj9juZbpRcbCBMD8wfvjWBi3GZCVd1pfYPmQdktCU1
    ih77O7MPn3DDQVcfZ1lYr9pETf2mprMdk0ytUzLsBjzGrA2mmvPJRQZZNJQqqiDP
    xjIk8/NwSHD5I4u25K3wK0DCnUWb6xGLAObSoengXctWDLaxnrt3HVLSw0yXXCqk
    dBva4rdAqxwS0p5zoqRlatqdmieg3zPorW+dPVNKk+mL0MvS0OQznoktPwThshfV
    Z7dc7g0FW9UAKliZxodnvtG+B2F1Rpz+aNOSqjdu42Eh+UlFvOS9BUTrRdaUUq+h
    UhqGhnZOfHFGPOvafFKraKsunxprR4ihJKfnDtf78NJJAZuU1rHGC1WaLhs2ZEUN
    RsIxXoDHskhxvkV0nxrsIfgCzK3U6DmTyy9yexvSRdDQGP1BmSgwnikp8QYzDtmF
    KD7j8YpCnxRrvg==
    =S7Lq
    -----END PGP MESSAGE-----
  "SECRET_KEY": |-
    -----BEGIN PGP MESSAGE-----
    Version: GnuPG v1.4.11 (GNU/Linux)

    hQEMAzBv9PsbguWNAQf/ROPyLLBgdMx6j63RBdYGCLeARJJqF3wm9NgnQeGHez4w
    Rfh9BR8yZABv4djqI9FMVJlkW7O4LvG2dIjfTVXtJmEGpnMg1sooB8jHJ/J8El2O
    4uj+ZmQ4LNYUW5UZHFGHPnzZTi8rrmRSgCxQBO2ZLFLC8MlWxyqXivM9gbLI+hPr
    gf/1JJvqCHdAcCw/ey40rq7dFk5Mj5mcp+K8jYw0u+Hocw/C/C38PkSET6e6hieV
    W/w+gzXZI0Foc8IE5NweiUql/f2wkthfO8M6mAi8Z6GI/lYXLeROBzxnIvz2LY5g
    FjEj1uTZi4mUFnKU2uc4wewxkzqBeQRdobp1YHb4JdJ7AYBuz7GEZaKstH2aljSC
    yCel3fy7PJO8xbsht4S/Hp/JoMPL6MApzq8DtSRoPPtCSKFEroDq1QDW1SEQYgUh
    X65z45cw9yreT+y+dAOei6WIAN6HkkliiMxIrHSOCphpghAArOs6LIWxdkdm1wat
    qsSRCTgqWcOq1DM4
    =JNt9
    -----END PGP MESSAGE-----
  "BROKER_PASSWORD": |-
    -----BEGIN PGP MESSAGE-----
    Version: GnuPG v1.4.11 (GNU/Linux)

    hQEMAzBv9PsbguWNAQf/brJN90xKdHjTOG8X8t00ex7oOGa9H62JotBKTcyKz3Dq
    Zfp4MkCy6MrbKHVV6nzv9PfX/miydtMLdnJzKqj4K9LRB+ndXDsb3aEfxJY0Qtop
    GiRfY2YuJOw2bP5QtPfMtMTWRWllnwT15SZflRXo8UyAFjO9CyZ0vfoMkkNznbsv
    a+D3TINSbiJU3nYyLwennRA3aRsrRbfk3lSaNSu5PtEPERddciAPcF2G0XKxZfhA
    x/rMWIkD4da4s+WyIGSdI5qpyEgsq1bC+t6Mn0rmC500kHSysh6sccM/rG0CIMBS
    tIrKxV5hZ/St5AMiDLdmEYnoe1HWOOzKopcOnJ4SAtJJAS23bczKIhxJ2OvRe24t
    EWt+Co93S5n3cqa42VIpqhyPOgqN0FZdmtny9B669waxFUN7WmJGbvJ5P3nJGTOs
    9gxxa8RS+DJ9dw==
    =AH05
    -----END PGP MESSAGE-----

# Private deploy key. Must be GPG encrypted.
github_deploy_key: |-
  -----BEGIN PGP MESSAGE-----
  Version: GnuPG v1.4.11 (GNU/Linux)

  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
  =aQpO
  -----END PGP MESSAGE-----

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
