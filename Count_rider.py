import os
import pandas as pd

# Change this to your base directory
base_dir = r"C:\Attendance\BLOCK_rider"

# Collect all Excel/CSV files from subfolders
all_files = []
for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.endswith(".xlsx") or file.endswith(".csv"):
            all_files.append(os.path.join(root, file))

# Ask user how many Rider IDs to search
num_riders = int(input("Enter number of Rider IDs: "))
rider_ids = []
for _ in range(num_riders):
    rider_ids.append(input("Enter Rider ID: ").strip())

# Dictionary to track results
rider_data = {rider_id: [] for rider_id in rider_ids}

# Process each file
for file_path in all_files:
    try:
        # Try reading both XLSX and CSV
        if file_path.endswith(".xlsx"):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)

        # Check if Rider ID column exists
        if "Rider ID" not in df.columns:
            continue

        for rider_id in rider_ids:
            if rider_id in df["Rider ID"].astype(str).values:
                date = os.path.basename(os.path.dirname(file_path))
                rider_data[rider_id].append(date)

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

# Create summary DataFrame
summary = []
for rider_id, dates in rider_data.items():
    summary.append({
        "Rider_ID": rider_id,
        "Dates": ", ".join(sorted(set(dates))),
        "Total Count": len(dates)
    })

result_df = pd.DataFrame(summary)
print(result_df)

# Optionally save the result
result_df.to_excel("rider_block_summary.xlsx", index=False)
