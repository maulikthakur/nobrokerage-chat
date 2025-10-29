# backend/api.py
from flask import Flask, request, jsonify
import pandas as pd
import re

app = Flask(__name__)

# -------------------------------
# Load CSVs (same logic as your working app.py)
# -------------------------------
PROJECT_CSV = "backend/data/project.csv"
ADDR_CSV = "backend/data/ProjectAddress.csv"
CONFIG_CSV = "backend/data/ProjectConfiguration.csv"
VARIANT_CSV = "backend/data/ProjectConfigurationVariant.csv"

project = pd.read_csv(PROJECT_CSV)
address = pd.read_csv(ADDR_CSV)
config = pd.read_csv(CONFIG_CSV)
variant = pd.read_csv(VARIANT_CSV)

# Map city IDs -> names (adjust mapping if you have more cityIds)
city_mapping = {
    "cmf6nu3ru000gvcxspxarll3v": "Pune",
    "cmf50r5a00000vcj0k1iuocuu": "Mumbai",
}
project["cityName"] = project["cityId"].map(city_mapping)

merged = project.merge(address, left_on="id", right_on="projectId", how="left", suffixes=("", "_addr"))
merged = merged.merge(config, left_on="id", right_on="projectId", how="left", suffixes=("", "_conf"))
merged = merged.merge(variant, left_on="id_conf", right_on="configurationId", how="left", suffixes=("", "_var"))

# normalize helper columns
merged['title'] = merged['projectName'].fillna('').astype(str)
merged['title_lower'] = merged['title'].str.lower()
merged['cityName_lower'] = merged['cityName'].fillna('').astype(str).str.lower()
merged['locality'] = merged['landmark'].fillna('').astype(str)
merged['locality_lower'] = merged['locality'].str.lower()
merged['bhk'] = merged['customBHK'].fillna('').astype(str)
merged['bhk_lower'] = merged['bhk'].str.lower()
merged['possession'] = merged['status'].fillna('').astype(str)
merged['possession_lower'] = merged['possession'].str.lower()
merged['price'] = pd.to_numeric(merged['price'], errors='coerce')

# -------------------------------
# Utilities: parsing & formatting
# -------------------------------
def parse_bhk(text: str):
    m = re.search(r'(\d+)\s*bhk', text.lower())
    return int(m.group(1)) if m else None

def parse_budget(text: str):
    t = text.lower().replace(',', '')
    # under / below / < X
    m = re.search(r'(?:under|below|<|upto|up to)\s*₹?\s*([\d\.]+)\s*(cr|crore|lakh|lac|l)?', t)
    if m:
        num = float(m.group(1)); unit = m.group(2) or ''
        if 'cr' in unit: return int(num * 1e7)
        if 'l' in unit: return int(num * 1e5)
        return int(num)
    # between X and Y
    m2 = re.search(r'between\s*₹?\s*([\d\.]+)\s*(cr|lakh|l)?\s*(?:and|-)\s*₹?\s*([\d\.]+)\s*(cr|lakh|l)?', t)
    if m2:
        def conv(n,u):
            n=float(n)
            if u and 'cr' in u: return int(n*1e7)
            if u and 'l' in u: return int(n*1e5)
            return int(n)
        return {'min': conv(m2.group(1), m2.group(2)), 'max': conv(m2.group(3), m2.group(4))}
    # bare number with unit
    m3 = re.search(r'₹?\s*([\d\.]+)\s*(cr|lakh|l)?', t)
    if m3:
        num=float(m3.group(1)); unit=m3.group(2) or ''
        if 'cr' in unit: return int(num * 1e7)
        if 'l' in unit: return int(num * 1e5)
        return int(num)
    return None

def parse_city(text: str):
    known = merged['cityName'].dropna().unique().tolist()
    t = text.lower()
    for c in known:
        if c and c.lower() in t:
            return c
    m = re.search(r'in\s+([A-Za-z\- ]+)', text, re.I)
    if m:
        return m.group(1).strip().split()[0].capitalize()
    return None

def parse_possession(text: str):
    t = text.lower()
    if 'ready' in t or 'ready to move' in t or 'ready-to-move' in t: return 'Ready'
    if 'under construction' in t or 'uc' in t: return 'Under Construction'
    return None

def parse_locality(text: str):
    m = re.search(r'(?:in|near|around|at)\s+([A-Za-z0-9\-\s]+)', text, re.I)
    if m:
        cand = m.group(1).strip()
        # return short locality (first 3 words)
        return ' '.join(cand.split()[:3])
    return None

def parse_project_name(text: str):
    t = text.lower()
    for title in merged['title_lower'].unique():
        if title and title in t:
            return merged.loc[merged['title_lower']==title, 'title'].iloc[0]
    return None

def format_price_rupee(v):
    if pd.isna(v): return None
    v = float(v)
    if v >= 1e7: return f"₹{round(v/1e7,2)} Cr"
    if v >= 1e5: return f"₹{round(v/1e5,2)} L"
    return f"₹{int(v)}"

# -------------------------------
# Core: extract filters & search
# -------------------------------
def extract_filters(query: str):
    return {
        'city': parse_city(query),
        'bhk': parse_bhk(query),
        'budget': parse_budget(query),
        'possession': parse_possession(query),
        'locality': parse_locality(query),
        'project_name': parse_project_name(query),
    }

def apply_filters(filters, max_results=10):
    df = merged.copy()
    # city
    if filters.get('city'):
        df = df[df['cityName'].str.lower() == str(filters['city']).lower()]
    # project name
    if filters.get('project_name'):
        pn = filters['project_name'].lower()
        df = df[df['title_lower'].str.contains(pn, na=False)]
    # locality
    if filters.get('locality'):
        loc = filters['locality'].lower()
        df = df[df['locality_lower'].str.contains(loc, na=False) | df['title_lower'].str.contains(loc, na=False)]
    # bhk
    if filters.get('bhk'):
        df = df[df['bhk_lower'].str.contains(str(filters['bhk']), na=False)]
    # possession
    if filters.get('possession'):
        poss = filters['possession'].lower()
        df = df[df['possession_lower'].str.contains(poss, na=False)]
    # budget: support dict (min/max) or single number in rupees
    b = filters.get('budget')
    if b:
        if isinstance(b, dict):
            minb = b.get('min', 0); maxb = b.get('max', 10**15)
            df = df[df['price'].between(minb, maxb)]
        else:
            # b is rupees max (from parse_budget "under 1.2Cr" -> 12000000)
            df = df[df['price'].fillna(0) <= float(b)]
    # drop duplicates and sort by price ascending
    df = df.drop_duplicates(subset=['id','configurationId'], keep='first')
    df = df.sort_values(by='price', ascending=True)
    return df.head(max_results)

def make_summary(df, filters):
    if df.empty:
        # graceful fallback: try relaxing locality or bhk if present
        fallback = "No matching properties found"
        if filters.get('city'): fallback += f" in {filters['city']}"
        if filters.get('bhk'): fallback += f" for {filters['bhk']}BHK"
        if filters.get('budget') and not isinstance(filters['budget'], dict):
            fallback += f" under {format_price_rupee(filters['budget'])}"
        fallback += ". Try broadening the search (remove locality or increase budget)."
        return fallback

    n = len(df)
    # top localities
    top_local = df['locality'].value_counts().head(3).to_dict()
    top_local_str = ', '.join([f"{loc} ({cnt})" for loc, cnt in top_local.items() if loc])
    # possession breakdown
    poss = df['possession'].value_counts().to_dict()
    poss_str = ', '.join([f"{k}: {v}" for k, v in poss.items()]) if poss else ''
    # price range
    minp = df['price'].min(); maxp = df['price'].max()
    price_range = f"{format_price_rupee(minp)} to {format_price_rupee(maxp)}"
    # amenities: gather aboutProperty tokens
    amens = []
    for s in df['aboutProperty'].fillna('').astype(str).tolist():
        amens += [a.strip() for a in re.split(r'[|,;.]', s) if a.strip()]
    amen_counts = {}
    for a in amens:
        amen_counts[a.lower()] = amen_counts.get(a.lower(), 0) + 1
    top_amen = ', '.join([a for a,_ in sorted(amen_counts.items(), key=lambda x:-x[1])[:3]])
    # Build 3-4 sentence summary (grounded only in CSV)
    sentences = []
    city_part = f"in {filters['city']}" if filters.get('city') else ''
    bhk_part = f"{filters['bhk']}BHK" if filters.get('bhk') else ''
    budget_part = ''
    if filters.get('budget') and not isinstance(filters['budget'], dict):
        budget_part = f" under {format_price_rupee(filters['budget'])}"
    sentences.append(f"{n} matching listings {city_part} for {bhk_part}{budget_part}.")
    if top_local_str:
        sentences.append(f"Top localities: {top_local_str}.")
    if top_amen:
        sentences.append(f"Common amenities include {top_amen}.")
    sentences.append(f"Prices range from {price_range}.")
    # join and limit to 4 sentences
    return " ".join([s for s in sentences[:4]])

def make_card(row):
    amenities = []
    # top source fields for amenities
    for field in ['aboutProperty', 'lift', 'parkingType']:
        val = row.get(field)
        if pd.notna(val) and str(val).strip():
            amenities.append(str(val))
    amenities = amenities[:3]
    slug = row.get('slug') or row.get('slugId') or row.get('projectName','')
    return {
        "title": row.get('projectName'),
        "city_locality": f"{row.get('cityName') or ''} • {row.get('landmark') or ''}".strip(' • '),
        "bhk": row.get('customBHK'),
        "price": format_price_rupee(row.get('price')),
        "project_name": row.get('projectName'),
        "possession_status": row.get('status'),
        "amenities": amenities,
        "cta_url": f"/project/{str(slug).lower().replace(' ','-')}"
    }

# -------------------------------
# API endpoint
# -------------------------------
@app.route("/search", methods=["POST"])
def search():
    payload = request.get_json(force=True)
    query = payload.get('query','')
    max_results = int(payload.get('max_results', 10))
    filters = extract_filters(query)
    df = apply_filters(filters, max_results=max_results)
    summary = make_summary(df, filters)
    cards = [make_card(row) for _, row in df.iterrows()]
    return jsonify({
        "summary": summary,
        "total_results": len(df),
        "results": cards
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
