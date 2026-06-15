import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parent
CSV_PATH = MODEL_DIR / "historical_orders.csv"

def train():
    print(f"Loading data from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    
    # Fill missing values for categorical columns
    df["delay_reason"] = df["delay_reason"].fillna("None")
    
    # Define features and target
    # As per instructions: Target variable y must be binary (0 or 1)
    # y = (sla_remaining < 0).astype(int) is same as (order_age_hours > sla_hours).astype(int)
    # The 'breached' column in CSV might already be this, but let's re-calculate to be safe.
    df["target"] = (df["order_age_hours"] > df["sla_hours"]).astype(int)
    y = df["target"]
    
    feature_cols = [
        "lens_type",
        "current_stage",
        "order_age_hours",
        "sla_hours",
        "inventory_available",
        "qc_failures",
        "store_location",
        "rework_count",
        "delay_reason",
    ]
    X = df[feature_cols].copy()
    
    # Encode categorical features
    encoders = {}
    for col in X.select_dtypes(include="object").columns:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col])
        encoders[col] = le
        
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"Training RandomForestClassifier on {len(X_train)} samples...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # Verify predict_proba works
    print("Verifying predict_proba works...")
    sample_proba = model.predict_proba(X_test[:1])
    print(f"Sample predict_proba output: {sample_proba}")
    
    # Save artifacts
    joblib.dump(model, MODEL_DIR / "sla_model.pkl")
    joblib.dump(encoders, MODEL_DIR / "encoders.pkl")
    print(f"Model and Encoders saved to {MODEL_DIR}")

if __name__ == "__main__":
    train()
