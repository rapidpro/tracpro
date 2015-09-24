#!yaml|gpg

environment: staging

domain: edutrac-staging.cakt.us

subdomains: ['afghanistan', 'caktus', 'car', 'guinea', 'malawi', 'mexico', 'peru', 'sierra-leone', 'uganda', 'zimbabwe']

repo:
  url: git@github.com:rapidpro/tracpro.git
  branch: master

# Additional public environment variables to set for the project
env:
  CSRF_COOKIE_DOMAIN: ".edutrac-staging.cakt.us"
  HOSTNAME: "edutrac-staging.cakt.us"
  SESSION_COOKIE_DOMAIN: ".edutrac-staging.cakt.us"
  SITE_HOST_PATTERN: "https://%s.edutrac-staging.cakt.us"


# Uncomment and update username/password to enable HTTP basic auth
# Password must be GPG encrypted.
http_auth:
  "caktus": |-
    -----BEGIN PGP MESSAGE-----
    Version: GnuPG v1.4.11 (GNU/Linux)

    hQEMA2qOOApeG3TpAQf/R6o+UbnDB/NgQccil8y/XwsNwOidD3XuVqcs1oah5MEi
    v6Ywl2Qonf5AlK7oy3mQUCGGOeEpAdXm7vWXquNKkuRw9NprXhSy0FssTWOCp7H3
    DgswMXjfkmnw1tE9NjE57AzwAnLzRp6HpuesMemWkQYX+Ylrp2OQRAvoeeSsEWes
    PeUVKgrcpI966ErUAhw481Nsu73Fm2kKzIVMmA/1241lpdQOjGao9tQ5ZnO4IPM2
    eqjWOetFlDkg0rOmVfkWt3ZTDtP1F7exj5eELtozdiLkL6vwwuiiPtOQPUhDqw68
    bHoeNNfeGXo9ZtNVS0KVudl2tb46jhR0w6p9geBsatJBATDNVeNiyL4jim7id8uw
    OU1O5HalaZ0PPBIgvop3+Fbktr8Tx825lei+JHfUdio9rUu8H83LjE/D4m9bLyk1
    WTA=
    =SB7w
    -----END PGP MESSAGE-----

# Private environment variables. Must be GPG encrypted.
secrets:
  "DB_PASSWORD": |-
    -----BEGIN PGP MESSAGE-----
    Version: GnuPG v1.4.11 (GNU/Linux)

    hQEMA2qOOApeG3TpAQgAq9QTNssRYNe3Der4FDBcv+1UwtoJYasuL0XbfPHmU5Ax
    uGYIjo3xNy1Ayk8TKYR0W+WEggLRVdj3Wtv5ZoVuH7hLV+aNLWf5hn1DbmHHX3K/
    ny5tQkfeP7ZKjcKt62qtDQF/75XJr4b+wiqqDZs+yrJsdkLRP2L5HoJkam+R/9dL
    3iRsh/XogY4x/j7vZnuyPOvq0/yOyNwuX1sqw5K9eXliFHSDrtMolnfHVYS05JXE
    e5nOfhCsKyvPDxr4j0Ekcv4wqAKGJOYIDP1pSTZ9k1FQFXSvhsvPePJemOZjis7B
    e0Xm2dCOFDAOPBYg0QLAHUVSND5ZHiFacupjDvRRx9JHAcM3v4XcrfehLigje3xM
    7UGp0rknxeqnhG/5h6/q8ImKqsomMOvArF+9tDDAuJ3eF9fLi9dR+QWHk8UYnlKS
    7PuxGKI+Rjg=
    =AVzP
    -----END PGP MESSAGE-----
  "SECRET_KEY": |-
    -----BEGIN PGP MESSAGE-----
    Version: GnuPG v1.4.11 (GNU/Linux)

    hQEMA2qOOApeG3TpAQgAlOAmJW2MkiuLxo1vJnwDZpxzT0iaZz4iCxQGff5w/JxJ
    H+kjlKUUgiaejomdjK1Sv6MsN/nIvHNYonFtYEXhQY4/oJ0V/4rBXBjGLryiUdpb
    ZYuZKXQwaztORRmzDFAw5ImKIgxsoAtJRt2PB3YhLLBd24PiNs4LCBdr+sZDywgH
    QyoAE2vLamqjSa+MnWkp5mZgh34sDLRcamIIfG9j2a6EvxB6g24XwqlMMUjNFj/6
    NPD002deqErQj/9BXcmaycXDHieC9p7SF1nZOGFt3G1uV4tVfMzQl18WIjAh/kRL
    OojkFYyQJfj7Rf/58VB8AmN3s1Z1n1oRwgKNOtjam9J7AdjkzqXBf+8+6LN8B4bk
    YiwNWJUm78NJEhptv7C6MA45Hj7R1RwQ8bK+bJtzFIUEzFo/uiKvwCn2B0ArV3qC
    QPhteBjjVUmAfqf14f/QIgW5IPNwJC7GaBi/FPIRCqs7mpEwiPH8/syrcpuhUhQE
    b4lpxnHuDcCi4uBv
    =C2Su
    -----END PGP MESSAGE-----

  "BROKER_PASSWORD": |-
    -----BEGIN PGP MESSAGE-----
    Version: GnuPG v1.4.11 (GNU/Linux)

    hQEMA2qOOApeG3TpAQf+NtexYylQA2Rc/MCXIH3ZRJhBPduzGMUI+a/GT1TziYFr
    duiubriDJZIPYovN+aUWeoSr36cR3l/wtRB43pzDun2qABXP8BLfT5+7N3Dp74z8
    IfC3L5j5uEBFL8PHSSxBCOLDF5qaBAQC8OgLgKzmhXNdIn85fsHhNqblgqc++kkT
    WjyWoePnNdUiaJmT4SDB3li+FqFGR690L2JNJdnUoMPvwCLO+FzBzUJmX98dCvR4
    np1vla1xwfiSijfbLus2uZjEzYMHF7LGQ+v63vJj5y/36+5KuL9Ggh9W9um7bzEB
    RZMw/WJJqtSIqRhkhyLJGXzAVsXV3djK+O4ywDwastJJAQctnjGcEQQfouXbONqY
    iBf01RZw4pgctAY/WQVLlbb1tX0BCH/yXJEURinFzT9fNhA2yX9l/DFT/zxZpPYu
    l3jtgVLZpqGo+Q==
    =z7Tk
    -----END PGP MESSAGE-----

# Private deploy key. Must be GPG encrypted.
github_deploy_key: |-
  -----BEGIN PGP MESSAGE-----
  Version: GnuPG v1.4.11 (GNU/Linux)

  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
  =5zNt
  -----END PGP MESSAGE-----

# Uncomment and update ssl_key and ssl_cert to enabled signed SSL
# Must be GPG encrypted.
#{% if 'balancer' in grains['roles'] %}
ssl_key: |
  -----BEGIN PGP MESSAGE-----
  Version: GnuPG v1.4.11 (GNU/Linux)

  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
  x1iUB8rnCt7wCCCy0/bm
  =Wt3w
  -----END PGP MESSAGE-----
ssl_cert: |
  -----BEGIN PGP MESSAGE-----
  Version: GnuPG v1.4.11 (GNU/Linux)

  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
  =usOu
  -----END PGP MESSAGE-----
#{% endif %}
