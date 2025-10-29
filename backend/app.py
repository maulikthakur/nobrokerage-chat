import pandas as pd
import re
from flask import Flask, request, jsonify
from flask_cors import CORS

# -------------------------------
# Load CSV files
# -------------------------------
project = pd.read_csv("backend/data/project.csv")
address = pd.read_csv("backend/data/ProjectAddress.csv")
config = pd.read_csv("backend/data/ProjectConfiguration.csv")
variant = pd.read_csv("backend/data/ProjectConfigurationVariant.csv")

# Example city mapping
city_mapping = {
    "cmf6nu3ru000gvcxspxarll3v": "Pune",
    "cmf50r5a00000vcj0k1iuocuu": "Mumbai",
}

# Add a readable city column
project["cityName"] = project["cityId"].map(city_mapping)

# -------------------------------
# Merge CSVs safely
# -------------------------------
merged = project.merge(address, left_on="id", right_on="projectId", how="left", suffixes=("", "_addr"))
merged = merged.merge(config, left_on="id", right_on="projectId", how="left", suffixes=("", "_conf"))
merged = merged.merge(variant, left_on="id_conf", right_on="configurationId", how="left", suffixes=("", "_var"))

print("✅ Data merged successfully!")
merged.to_csv("merged_projects.csv", index=False)
print("✅ Merged file saved as merged_projects.csv")
print("Total projects:", len(merged))
print("Columns:", list(merged.columns)[:10])
print(merged.head(2))

# -------------------------------
# Query Parser
# -------------------------------
def parse_query(query):
    query = query.lower()

    # Extract city
    cities = ["pune", "mumbai", "bangalore", "hyderabad", "delhi"]
    city = next((c for c in cities if c in query), None)

    # Extract BHK
    bhk_match = re.search(r'(\d+)\s*bhk', query)
    bhk = bhk_match.group(1) if bhk_match else None

    # Extract Budget
    budget_match = re.search(r'(\d+\.?\d*)\s*(cr|crore|l|lac|lakh)', query)
    budget = None
    if budget_match:
        value, unit = budget_match.groups()
        value = float(value)
        if unit.startswith('cr'):
            budget = value * 100  # convert Cr → Lakh
        else:
            budget = value

    return {"city": city, "bhk": bhk, "budget_lakh": budget}


# -------------------------------
# Property Search
# -------------------------------
def search_properties(query):
    filters = parse_query(query)
    city = filters["city"]
    bhk = filters["bhk"]
    budget_lakh = filters["budget_lakh"]

    df = merged.copy()

    # ✅ Apply combined filter (safer and cleaner)
    filtered = df[
        (df["cityName"].str.lower() == city.lower() if city else True)
        & (df["customBHK"].str.contains(bhk, case=False, na=False) if bhk else True)
        & (df["price"].fillna(0) <= budget_lakh * 100000 if budget_lakh else True)
    ]

    if filtered.empty:
        return {
            "summary": f"No {bhk}BHK options found under ₹{budget_lakh}L in {city.title() if city else 'selected area'}.",
            "results": []
        }

    # -------------------------------
    # Summary
    # -------------------------------
    avg_price = filtered["price"].mean() / 100000
    locations = filtered["landmark"].dropna().unique()[:3]
    summary = f"Found {len(filtered)} properties"
    if city:
        summary += f" in {city.title()}"
    if bhk:
        summary += f" with {bhk} BHK"
    if budget_lakh:
        summary += f" under ₹{budget_lakh}L"
    summary += f". Average price ~ ₹{avg_price:.2f}L. Top locations: {', '.join(locations)}."

    # -------------------------------
    # Format Results (Fixed Amenities)
    # -------------------------------
    results = []
    for _, row in filtered.head(5).iterrows():
        amenities_list = [row.get("lift"), row.get("parkingType")]
        amenities_clean = [str(a) for a in amenities_list if pd.notna(a) and str(a).lower() not in ["false", "0", "none"]]

        card = {
            "Project Name": row.get("projectName"),
            "BHK": row.get("customBHK"),
            "Price": f"₹{row.get('price')/100000:.2f} L" if pd.notna(row.get("price")) else "N/A",
            "Locality": row.get("landmark"),
            "Status": row.get("status"),
            "Amenities": ", ".join(amenities_clean) if amenities_clean else "N/A"
        }
        results.append(card)

    return {"summary": summary, "results": results}


# -------------------------------
# Test Search
# -------------------------------
user_query = "3BHK flat in Pune under ₹1.2 Cr"
response = search_properties(user_query)

print("\n🏡 Summary:")
print(response["summary"])
print("\n📋 Top Results:")
for r in response["results"]:
    print(r)

print("\n🧾 Unique cities in dataset:")
print(merged["cityId"].dropna().unique())

print("\n🏠 Unique BHK values:")
print(merged["customBHK"].dropna().unique())

print("\n💰 Price range:")
print(f"Min: {merged['price'].min()}  Max: {merged['price'].max()}")

app = Flask(__name__)
CORS(app)

# ✅ Load merged data
merged = pd.read_csv("merged_projects.csv")  # Or your processed file

# ✅ Query parser (already working)
def parse_query(query):
    city_match = re.search(r"(pune|mumbai|nagpur|delhi)", query, re.I)
    bhk_match = re.search(r"(\d\s?bhk)", query, re.I)
    budget_match = re.search(r"(\d+(\.\d+)?)(\s?cr|crore|lakh|lakhs?)", query, re.I)

    city = city_match.group(1) if city_match else None
    bhk = bhk_match.group(1).replace(" ", "").upper() if bhk_match else None
    budget_lakh = None
    if budget_match:
        value = float(budget_match.group(1))
        unit = budget_match.group(3).lower()
        if "cr" in unit or "crore" in unit:
            budget_lakh = value * 100
        elif "lakh" in unit:
            budget_lakh = value
    return {"city": city, "bhk": bhk, "budget_lakh": budget_lakh}

# ✅ Search logic
def search_properties(query):
    filters = parse_query(query)
    city = filters.get("city")
    bhk = filters.get("bhk")
    budget_lakh = filters.get("budget_lakh")

    if not (city and bhk and budget_lakh):
        return {"message": "Please provide city, BHK, and budget in your query."}

    filtered = merged[
        (merged["cityName"].str.lower() == city.lower())
        & (merged["customBHK"].str.contains(bhk, case=False, na=False))
        & (merged["price"] <= budget_lakh * 100000)
    ]

    if filtered.empty:
        return {
            "message": f"No matching properties found in {city.title()} for {bhk} under ₹{budget_lakh/100:.1f} Cr. Try broadening the search."
        }

    results = []
    for _, row in filtered.head(5).iterrows():
        amenities = [str(a) for a in [row.get("lift"), row.get("parkingType")] if pd.notna(a)]
        results.append({
            "projectName": row["projectName"],
            "city": row["cityName"],
            "bhk": row["customBHK"],
            "price": f"₹{row['price']:,}",
            "status": row.get("status", "N/A"),
            "amenities": ", ".join(amenities),
            "url": f"/project/{row['slug']}"
        })

    return {"message": f"Found {len(results)} results for {bhk} in {city.title()} under ₹{budget_lakh/100:.1f} Cr.", "results": results}

# ✅ API route
@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "")
    response = search_properties(user_input)
    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True)