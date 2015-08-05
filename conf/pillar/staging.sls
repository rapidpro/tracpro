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
# {% if 'balancer' in grains['roles'] %}
# ssl_key: |
# -----BEGIN PGP MESSAGE-----
# -----END PGP MESSAGE-----
#
# ssl_cert: |
# -----BEGIN PGP MESSAGE-----
# -----END PGP MESSAGE-----
# {% endif %}
