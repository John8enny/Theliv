# Theliv

> **A decentralized digital evidence management system** 🔐📁

Theliv is a professional, decentralized evidence management portal built using **Hyperledger Fabric**, **Django**, **IPFS**, and **Apache Tika**. 
Designed for organizations like Police, Judiciary, and Forensic departments, Theliv offers a secure and verifiable system for adding, transferring, 
and auditing digital evidence using blockchain and distributed file systems.


## 🚀 Features

- Submit and preview digital evidence (image, video, PDF, etc.)
- Secure content addressing using IPFS
- Evidence hash verification
- User roles via Django Groups (Police, Judiciary, Forensic)
- Chaincode-backed audit trail
- Transfer system with access control

## 🌐 Ports Guide

| Component             | Port  | Description                    |
|----------------------|-------|--------------------------------|
| Django Web Server    | 8000  | Main frontend and REST views   |
| Fablo API Server     | 3000  | Blockchain REST API gateway    |
| IPFS Daemon          | 5001  | IPFS API port                  |
| IPFS Gateway         | 8080  | Web access to IPFS files       |
| Apache Tika Server   | 9998  | File metadata extraction       |
| PostgreSQL           | 5432  | Database                       |

## 🛠️ Setup Instructions

```bash
# 1. Start Hyperledger Fabric network using Fablo
fablo up

# 2. Start the Fablo REST API server
node index.js

# 3. Download and run Apache Tika server
wget https://dlcdn.apache.org/tika/3.1.0/tika-server-standard-3.1.0.jar
java -jar tika-server-standard-3.1.0.jar --port 9998

# 4. Start IPFS daemon
ipfs daemon
```

### Django Setup

```bash
# Create virtual environment and install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure PostgreSQL in settings.py
# Make migrations and create admin
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# Run Django server
python manage.py runserver
```

## 📡 API Documentation

These endpoints are exposed through the `index.js` Fablo REST API layer.

### `POST /evidence/add`
Submit new evidence to the blockchain.

```json
{
  "evidenceId": "EV123",
  "evidenceName": "Laptop",
  "caseId": "CASE789",
  "hash": "abc123",
  "ipfsHash": "QmXYZ...",
  "owner": "admin",
  "uploader": "john_django",
  "metadata": {
    "file_name": "laptop.png",
    "file_size": 12345,
    "uploaded_at": "2025-04-01T10:00:00Z"
  },
  "customdata": {
    "model": "Dell",
    "serial": "XPS9380"
  },
  "evidenceType": "image",
  "format": "JPG"
}
```

### `POST /evidence/transfer`
Transfer evidence to another user.

```json
{
  "evidenceId": "EV123",
  "to": "jane_judiciary"
}
```

### `GET /evidence/audit/:evidenceId`
Returns the full transfer history of the specified evidence.

### `GET /evidence/:caseId`
Fetch all evidence under a specific case.


## 📃 License & Acknowledgements

This project is built with:

- [Hyperledger Fabric](https://www.hyperledger.org/use/fabric)
- [IPFS](https://ipfs.io/)
- [Django](https://www.djangoproject.com/)
- [Apache Tika](https://tika.apache.org/)

[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Developed by John8enny ⚙️
