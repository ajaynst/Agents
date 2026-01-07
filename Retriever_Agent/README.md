### POSTGRES DB

check if postgres service is running: 

```bash
service postgresql status
```

1. default postgres user and open psql shell:

```bash
sudo -u postgres psql
```

2. put new password for user: 

```bash
ALTER USER postgres PASSWORD 'your_secure_password';
```
3. Exit postgres cmd: `\q`

ref: https://www.cantech.in/knowledge-base/how-to-install-postgresql-on-ubuntu-24-04/
