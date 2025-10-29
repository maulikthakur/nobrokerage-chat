🏡 NoBrokerage Chat — AI-Powered Real Estate Search Assistant

📖 Overview
**NoBrokerage Chat** is an intelligent real estate assistant designed to help users discover property listings through natural language conversations.  
Instead of using complex filters or dropdown menus, users can simply type queries like:

> “Show me 3BHK flats in Pune under ₹1.2 Crore”
and the system automatically interprets the message, filters property data, and returns the most relevant results.
This project demonstrates how **AI-driven chat interfaces** can simplify user interaction with structured data — making property discovery faster, smarter, and more intuitive.
---

🎯 Objective
The main goal of **NoBrokerage Chat** is to provide an easy and interactive way for users to:
- Search for real estate properties through conversational input.
- Get structured results with project name, price, BHK type, and location.
- Explore projects without navigating through multiple filters.
- Learn how AI and data processing can enhance search experience.
This project combines **data engineering, backend APIs, and a frontend chat interface** into one cohesive system.
---

⚙️ System Architecture
The architecture of **NoBrokerage Chat** consists of two major parts:
1️⃣ Backend (Flask + Python)
Handles:
- Merging and cleaning property datasets.
- Parsing user messages.
- Extracting key details like **city, budget, and BHK type**.
- Filtering CSV data accordingly.
- Returning structured JSON responses to the frontend.

2️⃣ Frontend (React.js)
Handles:
- Rendering an interactive **chat interface**.
- Sending user messages to the backend API.
- Displaying formatted property results with prices, status, and locality.
---

🧠 Core Concept
At the heart of the system lies **Natural Query Interpretation**.  
When a user types a sentence like:
> “2 BHK apartment in Mumbai under 80 lakhs”

the backend:
1. Breaks down the message into components:
   - **City:** Mumbai  
   - **BHK:** 2 BHK  
   - **Budget:** ₹80 Lakhs  
2. Filters property data from the merged CSV file.
3. Calculates relevant statistics (e.g., average price, top localities).
4. Returns the result as a JSON response.

This design eliminates the need for complex NLP models, instead focusing on **rule-based extraction** and **data-driven responses** for accuracy and simplicity.
---

📊 Data Handling
Data Source
The project uses one or more CSV files containing property listings, merged into a single file named:
merged_projects.csv
markdown
Copy code

Columns
Each record typically includes:
- **projectName** – Name of the real estate project  
- **bhkType** – Property configuration (1BHK, 2BHK, 3BHK, etc.)  
- **city** – Location of the project  
- **price** – Property price in INR  
- **status** – UNDER_CONSTRUCTION / READY_TO_MOVE  
- **locality** – Exact area or neighborhood  

Merging Process
When the backend starts, it:
1. Scans multiple source files in the `/data` directory.
2. Combines them into one unified dataset.
3. Removes duplicates and missing values.
4. Saves the merged file as `merged_projects.csv`.

This ensures that all property information is readily available and clean for fast querying.
---

💻 Backend — Flask API Explanation

Key Components:
1. **Flask App Initialization**
   - Sets up the server and CORS to allow frontend communication.

2. **/chat Endpoint**
   - Accepts POST requests containing user messages in JSON format.
   - Parses and filters property data.
   - Returns structured results.

3. **Filter Logic**
   - Detects keywords like `1BHK`, `2BHK`, `3BHK`, etc.
   - Extracts city names and budget ranges.
   - Filters dataset accordingly using pandas.

4. **Response Structure**
   - Returns JSON with:
     - Summary message
     - List of filtered projects
     - Additional data insights (like average price, location trends)

For Live Demo : https://drive.google.com/file/d/1onpXDVkWGx18wscFRAmYoeW6seiJeBUL/view?usp=drivesdk
Example:
```json
{
  "message": "Found 2 results for 3BHK in Pune under ₹1.2 Cr.",
  "results": [
    {
      "projectName": "The Silver Altair",
      "price": "₹1.1 Cr",
      "bhk": "3BHK",
      "city": "Pune",
      "status": "UNDER_CONSTRUCTION",
      "amenities": "N/A"
    }
  ]
}

