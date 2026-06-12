import os
import json
import pandas as pd
import subprocess

# Define absolute filepaths
BASE_DIR = r"E:\Productivity-tracker"
EXCEL_PATH = os.path.join(BASE_DIR, "Poductivity_Tracker.xlsx")
JSON_PATH = os.path.join(BASE_DIR, "data.json")

def parse_excel_to_json():
    print("🔄 Accessing master Excel matrix...")
    if not os.path.exists(EXCEL_PATH):
        print(f"❌ Error: Could not locate Excel template at: {EXCEL_PATH}")
        return False
        
    # Read Excel sheet safely
    df = pd.read_excel(EXCEL_PATH, sheet_name=0)
    
    # Strip whitespace from column names to prevent mapping errors
    df.columns = df.columns.str.strip()
    
    # Drop completely empty rows
    df = df.dropna(how='all')
    
    database = []
    
    for _, row in df.iterrows():
        # Safeguard: Verify date existence
        if pd.isna(row['Date']):
            continue
            
        # Standardize date to string YYYY-MM-DD
        date_str = str(row['Date']).split(' ')[0]
        
        # 1. Structure Academic Section dynamically
        sub_key = str(row['Mock_Subject']).strip().lower() if not pd.isna(row['Mock_Subject']) else None
        
        academic_data = {
            "english": None,
            "arithmetic": None,
            "ga": None,
            "reasoning": None
        }
        
        # Map specific subject if scores are populated
        if sub_key in academic_data and not pd.isna(row['Total_Marks']) and not pd.isna(row['Marks_Obtained']):
            tot = float(row['Total_Marks'])
            obt = float(row['Marks_Obtained'])
            att = float(row['Total_Attempt']) if not pd.isna(row['Total_Attempt']) else obt
            wrg = float(row['Wrong_Answers']) if not pd.isna(row['Wrong_Answers']) else 0.0
            
            # Formulate baseline logic based on standard requirements
            base_targets = {"english": 35.0, "arithmetic": 20.0, "ga": 25.0, "reasoning": 22.0}
            baseline = base_targets.get(sub_key, 35.0)
            
            accuracy = round(( (att - wrg) / att ) * 100, 1) if att > 0 else 100.0
            
            academic_data[sub_key] = {
                "mock_desc": str(row['Mock_Name']) if not pd.isna(row['Mock_Name']) else "Sectional Assessment",
                "total_marks": tot,
                "marks_obtained": obt,
                "total_attempt": att,
                "wrong_answers": wrg,
                "accuracy": accuracy,
                "baseline": baseline
            }

        # 2. Structure Shorthand Section
        shorthand_data = None
        if not pd.isna(row['Topic']) or not pd.isna(row['Speed(WPM)']):
            shorthand_data = {
                "topic": str(row['Topic']) if not pd.isna(row['Topic']) else "Dictation Drill",
                "speed_wpm": float(row['Speed(WPM)']) if not pd.isna(row['Speed(WPM)']) else 80.0,
                "accuracy": float(row['Accuracy(%)']) if not pd.isna(row['Accuracy(%)']) else 100.0,
                "word_count": float(row['Word_Count']) if not pd.isna(row['Word_Count']) else 0.0,
                "notes": str(row['Notes']) if not pd.isna(row['Notes']) else ""
            }

        # 3. Structure Miscellaneous Habits Section (Mapping 1, 0, or B)
        def map_habit(val):
            val_str = str(val).strip().upper()
            if val_str in ['1', '1.0', 'Y', 'PRESENT']: return 'present'
            if val_str in ['B', 'BREAK', 'PLANNED_BREAK']: return 'planned_break'
            return 'absent'

        miscellaneous_data = {
            "english_vocabulary": map_habit(row.get('Eng_Vocab', 0)),
            "typing_practice": map_habit(row.get('Typing_Practice', 0)),
            "computer": map_habit(row.get('Computer', 0)),
            "shorthand_stroke": map_habit(row.get('Shorthand_Stroke', 0))
        }

        # Compile chronological day node
        day_node = {
            "date": date_str,
            "academic_data": academic_data,
            "shorthand_data": shorthand_data,
            "miscellaneous_data": miscellaneous_data
        }
        database.append(day_node)
        
    # Sort database by date descending to prioritize fresh logs at the top
    database.sort(key=lambda x: x['date'], reverse=True)
    
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=4)
        
    print(f"✅ Success: Synced {len(database)} records into database profile.")
    return True

def push_to_cloud():
    print("🚀 Commencing background cloud pipeline push...")
    try:
        os.chdir(BASE_DIR)
        subprocess.run(["git", "add", "data.json"], check=True)
        subprocess.run(["git", "commit", "-m", "sync ledger profile metrics"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("🎯 Cloud sync successful. Analytics portal initialized live.")
    except Exception as e:
        print(f"⚠️ Git core push deferred or encountered validation mismatch: {e}")

if __name__ == "__main__":
    if parse_excel_to_json():
        push_to_cloud()