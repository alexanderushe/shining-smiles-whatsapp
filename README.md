# Shining Smiles WhatsApp System

A lightweight Flask app for sending WhatsApp payment confirmations and balance reminders using Twilio and the Shining Smiles SMS API.

**📦 Repo**: https://github.com/alexanderushe/shining-smiles-whatsapp  
**📲 Twilio WhatsApp**: +14155238886 (sandbox)  
**📞 Test Receiver**: +263711206287

---

## 🚀 Features

- Send payment confirmations via WhatsApp
- Send balance reminders (cron scheduler)
- Integrates with Shining Smiles internal SMS API
- (Coming soon) Chatbot for inbound messages

---

## ⚙️ Setup Environment

1. **Clone Repository**
   ```bash
   git clone https://github.com/alexanderushe/shining-smiles-whatsapp.git
   cd shining-smiles-whatsapp

2. **Create and Activate Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
3. **▶️ Run the App**
   ```bash
   python app.py

4. **Database**
   ```bash
   psql -U postgres -h localhost -d shining_smiles
