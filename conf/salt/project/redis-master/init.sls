redis-server:
    pkg.installed:
      - name: redis-server
    service.running:
      - name: redis-server
      - enable: True
      - require:
        - pkg: redis-server
    file.replace:
      - name: /etc/redis/redis.conf
      - pattern: "^bind 127.0.0.1"
      - repl: "# bind 127.0.0.1"
      - require:
        - pkg: redis-server