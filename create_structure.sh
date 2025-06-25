#!/bin/bash

# Base project directory
mkdir -p shining-smiles-whatsapp/{logs,src/api,src/services,src/utils,tests}

# Create main files
touch shining-smiles-whatsapp/{app.py,config.py,requirements.txt,Procfile,.gitignore,.env,README.md}

# Create log file
touch shining-smiles-whatsapp/logs/app.log

# Create __init__.py files
touch shining-smiles-whatsapp/src/__init__.py
touch shining-smiles-whatsapp/src/api/__init__.py
touch shining-smiles-whatsapp/src/api/sms_client.py
touch shining-smiles-whatsapp/src/services/__init__.py
touch shining-smiles-whatsapp/src/services/payment_service.py
touch shining-smiles-whatsapp/src/services/reminder_service.py
touch shining-smiles-whatsapp/src/utils/__init__.py
touch shining-smiles-whatsapp/src/utils/logger.py
touch shining-smiles-whatsapp/src/utils/scheduler.py
touch shining-smiles-whatsapp/src/utils/whatsapp.py
touch shining-smiles-whatsapp/tests/__init__.py
touch shining-smiles-whatsapp/tests/test_sms_client.py

# Output completion
echo "✅ Project structure created under shining-smiles-whatsapp/"
