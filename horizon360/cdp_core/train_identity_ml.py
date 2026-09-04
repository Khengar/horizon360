import os
import random
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from difflib import SequenceMatcher
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import pickle

def scrape_names():
    """Scrapes a public table of companies from Wikipedia to generate a realistic synthetic dataset."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'class': 'wikitable'})
    
    companies = []
    if table:
        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td')
            if len(cols) > 1:
                # Clean up the company name for email domains
                comp = cols[1].text.strip()
                comp = comp.split(' ')[0].replace(',', '').replace('.', '')
                if comp:
                    companies.append(comp)
                
    # Fallback if scraping failed
    if not companies:
        companies = ["Acme", "Globex", "Initech", "Umbrella", "Stark", "Wayne"]
    
    first_names = ["John", "Sarah", "Michael", "Emma", "David", "James", "Elena", "Sophia", "Daniel", "Olivia", "Lucas", "Mia", "Alexander", "Charlotte"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Lee", "Walker", "Hall", "Allen"]
    
    profiles = []
    # Generate 1500 base identities
    for _ in range(1500):
        first = random.choice(first_names)
        last = random.choice(last_names)
        company = random.choice(companies)
        email = f"{first.lower()}.{last.lower()}@{company.lower()}.com"
        phone = f"+1{random.randint(200,999)}{random.randint(1000000,9999999)}"
        profiles.append({"name": f"{first} {last}", "email": email, "phone": phone})
        
    return profiles

def introduce_typo(text):
    if not text or len(text) < 3: return text
    idx = random.randint(0, len(text)-2)
    # swap two characters (transposition typo)
    chars = list(text)
    chars[idx], chars[idx+1] = chars[idx+1], chars[idx]
    return "".join(chars)

def generate_pairs(base_profiles):
    """Generates True Matches (Label = 1) and False Matches (Label = 0)"""
    data = []
    
    # 1. True Matches (perturbations)
    for p in base_profiles:
        p_match = p.copy()
        # Introduce noise to create a realistic duplicate
        if random.random() < 0.6:
            p_match["name"] = introduce_typo(p["name"])
        if random.random() < 0.3:
            p_match["email"] = p["email"].replace(".com", ".net")
        if random.random() < 0.4:
            p_match["phone"] = p["phone"][:-2] + str(random.randint(10,99))
            
        data.append((p, p_match, 1))
        
    # 2. False Matches
    # For every true match, add a random false match to balance the dataset
    for i in range(len(base_profiles)):
        p1 = base_profiles[i]
        p2 = random.choice(base_profiles)
        if p1["email"] != p2["email"]:
            data.append((p1, p2, 0))
            
    return data

def string_sim(a, b):
    if not a or not b: return 0.0
    return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()

def compute_features(p1, p2):
    """
    Computes the feature vector used by the ML model.
    Matches the deterministic feature heuristics used in the identity resolution pipeline.
    """
    # 1. Name similarity
    name_sim = string_sim(p1.get("name"), p2.get("name"))
    
    # 2. Email local similarity
    e1 = p1.get("email", "").split('@')[0] if '@' in p1.get("email", "") else ''
    e2 = p2.get("email", "").split('@')[0] if '@' in p2.get("email", "") else ''
    email_local_sim = string_sim(e1, e2)
    
    # 3. Email domain match
    d1 = p1.get("email", "").split('@')[1] if '@' in p1.get("email", "") else ''
    d2 = p2.get("email", "").split('@')[1] if '@' in p2.get("email", "") else ''
    domain_match = 1.0 if (d1 and d2 and d1 == d2) else 0.0
    
    # 4. Phone similarity
    # Simple check for same last 7 digits
    ph1 = p1.get("phone", "")[-7:]
    ph2 = p2.get("phone", "")[-7:]
    phone_sim = 1.0 if (ph1 and ph2 and ph1 == ph2) else string_sim(p1.get("phone"), p2.get("phone"))
    
    return [name_sim, email_local_sim, domain_match, phone_sim]

def main():
    print("==================================================")
    print(" CDP 360: ML Identity Resolution Training Pipeline")
    print("==================================================")
    
    print("\n[1/5] Scraping dataset from web (Wikipedia S&P 500)...")
    profiles = scrape_names()
    print(f"      Scraped {len(profiles)} base profiles.")
    
    print("\n[2/5] Generating match/non-match pairs with noise...")
    pairs = generate_pairs(profiles)
    random.shuffle(pairs)
    print(f"      Generated {len(pairs)} pairs for training.")
    
    print("\n[3/5] Computing feature vectors...")
    X = []
    y = []
    for p1, p2, label in pairs:
        X.append(compute_features(p1, p2))
        y.append(label)
        
    X = np.array(X)
    y = np.array(y)
    
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("\n[4/5] Training RandomForestClassifier...")
    clf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    clf.fit(X_train, y_train)
    
    print("\n[5/5] Evaluating model on validation set...")
    y_pred = clf.predict(X_val)
    acc = accuracy_score(y_val, y_pred)
    print(f"      Validation Accuracy: {acc * 100:.2f}%\n")
    print("Classification Report:")
    print(classification_report(y_val, y_pred))
    
    # Save the model
    model_path = os.path.join(os.path.dirname(__file__), "ml_identity_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(clf, f)
        
    print(f"✅ Model saved successfully to {model_path}")
    print("   The Identity Batch Pipeline will now use this model for confidence scoring.")

if __name__ == "__main__":
    main()
