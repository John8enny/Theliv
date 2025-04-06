# Theliv
Decentralized Evidence Portal

`fablo up` to up the Hyperledger fabric network

'node index.js' to start the api server

`wget https://dlcdn.apache.org/tika/3.1.0/tika-server-standard-3.1.0.jar` to download tika server
'java -jar gtika-server-standard-3.1.0.jar --port 9998' to start the apache tika server

`ipfs daemon` to start ipfs server

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
