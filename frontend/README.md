# 🏡 NoBrokerage Chat — AI-Powered Real Estate Assistant

**NoBrokerage Chat** is an intelligent property discovery platform that allows users to chat naturally to find real estate listings.  
Users can ask queries like:  
> “Show me 3BHK flats in Pune under ₹1.2 Cr”  

and instantly get relevant project results from structured data.

---

## 🚀 Tech Stack

### 🧠 Backend
- **Python (Flask)** — Handles chat requests and data processing  
- **Pandas** — Cleans and merges property data from CSV  
- **JSON API** — Serves structured responses to frontend queries  

### 💻 Frontend
- **React.js** — Interactive chat interface  
- **Fetch API** — Sends messages to backend and displays AI responses  
- **Simple custom CSS UI** — Clean and fast, without extra dependencies  

---

## ⚙️ Setup Guide

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/maulikthakur/nobrokerage-chat.git
cd nobrokerage-chat

cd backend
python -m venv venv
venv\Scripts\activate       # For Windows
pip install -r requirements.txt
python app.py

cd ../frontend
npm install
npm start
