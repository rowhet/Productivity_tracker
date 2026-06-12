import os
import json
import pandas as pd
import subprocess

# Absolute paths
BASE_DIR = r"E:\Productivity-tracker"
EXCEL_PATH = os.path.join(BASE_DIR, "Poductivity_Tracker.xlsx")
JSON_PATH = os.path.join(BASE_DIR, "data.json")

def parse_excel_to_json():
    print("🔄 Accessing master Excel matrix...")
    if not os.path.exists(EXCEL_PATH):
        print(f"❌ Error: Could not locate Excel template at: {EXCEL_PATH}")
        return False
        
    # Read Excel sheet
    df = pd.read_excel(EXCEL_PATH, sheet_name=0)
    df.columns = df.columns.str.strip()
    df = df.dropna(how='all')
    
    database = []
    
    for _, row in df.iterrows():
        if pd.isna(row['Date']):
            continue
            
        date_str = str(row['Date']).split(' ')[0]
        
        # 1. Map Subject Data Blocks explicitly from their own side-by-side columns
        academic_data = {
            "english": None,
            "arithmetic": None, # Kept placeholder for matching dashboard sidebars
            "ga": None,
            "reasoning": None
        }
        
        # English Parser
        if not pd.isna(row.get('Eng_Total')) and not pd.isna(row.get('Eng_Obtained')):
            academic_data["english"] = {
                "mock_desc": str(row['Eng_Mock_Desc']) if not pd.isna(row.get('Eng_Mock_Desc')) else "English Mock",
                "total_marks": float(row['Eng_Total']),
                "marks_obtained": float(row['Eng_Obtained']),
                "total_attempt": float(row['Eng_Attempts']) if not pd.isna(row.get('Eng_Attempts')) else float(row['Eng_Obtained']),
                "wrong_answers": float(row['Eng_Wrong']) if not pd.isna(row.get('Eng_Wrong')) else 0.0,
                "accuracy": float(row['Eng_Accuracy']) if not pd.isna(row.get('Eng_Accuracy')) else 100.0,
                "baseline": float(row['Eng_Baseline']) if not pd.isna(row.get('Eng_Baseline')) else 35.0
            }

        # Reasoning Parser (Mapping Res_ to Reasoning)
        if not pd.isna(row.get('Res_Total')) and not pd.isna(row.get('Res_Obtained')):
            academic_data["reasoning"] = {
                "mock_desc": str(row['Res_Mock_Desc']) if not pd.isna(row.get('Res_Mock_Desc')) else "Reasoning Mock",
                "total_marks": float(row['Res_Total']),
                "marks_obtained": float(row['Res_Obtained']),
                "total_attempt": float(row['Res_Attempts']) if not pd.isna(row.get('Res_Attempts')) else float(row['Res_Obtained']),
                "wrong_answers": float(row['Res_Wrong']) if not pd.isna(row.get('Res_Wrong')) else 0.0,
                "accuracy": float(row['Res_Accuracy']) if not pd.isna(row.get('Res_Accuracy')) else 100.0,
                "baseline": float(row['Res_Baseline']) if not pd.isna(row.get('Res_Baseline')) else 35.0
            }

        # General Awareness Parser
        if not pd.isna(row.get('GA_Total')) and not pd.isna(row.get('GA_Obtained')):
            academic_data["ga"] = {
                "mock_desc": str(row['GA_Mock_Desc']) if not pd.isna(row.get('GA_Mock_Desc')) else "GA Mock",
                "total_marks": float(row['GA_Total']),
                "marks_obtained": float(row['GA_Obtained']),
                "total_attempt": float(row['GA_Attempts']) if not pd.isna(row.get('GA_Attempts')) else float(row['GA_Obtained']),
                "wrong_answers": float(row['GA_Wrong']) if not pd.isna(row.get('GA_Wrong')) else 0.0,
                "accuracy": float(row['GA_Accuracy']) if not pd.isna(row.get('GA_Accuracy')) else 100.0,
                "baseline": float(row['GA_Baseline']) if not pd.isna(row.get('GA_Baseline')) else 35.0
            }

        # 2. Map Shorthand Data Block
        shorthand_data = None
        if not pd.isna(row.get('Shorthand_Topic')) or not pd.isna(row.get('Shorthand_WPM')):
            shorthand_data = {
                "topic": str(row['Shorthand_Topic']) if not pd.isna(row['Shorthand_Topic']) else "Dictation Drill",
                "speed_wpm": float(row['Shorthand_WPM']) if not pd.isna(row['Shorthand_WPM']) else 80.0,
                "accuracy": float(row['Shorthand_Accuracy']) if not pd.isna(row['Shorthand_Accuracy']) else 100.0,
                "word_count": float(row['Shorthand_Count']) if not pd.isna(row['Shorthand_Count']) else 0.0,
                "notes": str(row['Remarks']) if not pd.isna(row['Remarks']) else ""
            }

        # 3. Map Habit Data Block
        def map_habit(val):
            val_str = str(val).strip().upper()
            if val_str in ['1', '1.0', 'Y', 'PRESENT']: return 'present'
            if val_str in ['B', 'BREAK', 'PLANNED_BREAK']: return 'planned_break'
            return 'absent'

        miscellaneous_data = {
            "english_vocabulary": map_habit(row.get('Habit_Vocab', 0)),
            "typing_practice": map_habit(row.get('Habit_Typing', 0)),
            "computer": map_habit(row.get('Habit_Computer', 0)),
            "shorthand_stroke": map_habit(row.get('Habit_Stroke', 0))
        }

        day_node = {
            "date": date_str,
            "academic_data": academic_data,
            "shorthand_data": shorthand_data,
            "miscellaneous_data": miscellaneous_data
        }
        database.append(day_node)
        
    database.sort(key=lambda x: x['date'], reverse=True)
    
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=4)
        
    print(f"✅ Success: Processed records into data.json layout.")
    return True

def push_to_cloud():
    print("🚀 Commencing cloud upload...")
    try:
        os.chdir(BASE_DIR)
        subprocess.run(["git", "add", "data.json"], check=True)
        subprocess.run(["git", "commit", "-m", "sync custom horizontal matrix rows"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("🎯 Cloud update successful!")
    except Exception as e:
        print(f"⚠️ Git synchronization report: {e}")

if __name__ == "__main__":
    if parse_excel_to_json():
        push_to_cloud()