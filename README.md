# Theliv
Decentralized Evidence Portal

```bash
fablo up
```
to up the Hyperledger fabric network

```bash
node index.js
```
to start the api server

```bash
wget https://dlcdn.apache.org/tika/3.1.0/tika-server-standard-3.1.0.jar
```
to download tika server run 
```bash
java -jar gtika-server-standard-3.1.0.jar --port 9998
```
to start the apache tika server

```bash
ipfs daemon
```
to start ipfs server

start a venv
install requirement.txt
create superuser
setup postgress serever
edit database credentials in settings.py
if any changes in port, then make them in the appropriate files
then RUN
`python manage.py makemigrations`
`python manage.py migrate`
`python manage.py runserver`
