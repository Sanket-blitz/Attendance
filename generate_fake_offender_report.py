import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as XLImage

# Set base directory
base_dir = r"C:\Attendance\BLOCK_rider"

# Collect all Excel/CSV paths
file_paths = []
for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.endswith(('.xlsx', '.csv')) and not file.startswith('~$'):
            file_paths.append(os.path.join(root, file))

# Load and combine data
rider_data = pd.DataFrame()
for file in file_paths:
    try:
        df = pd.read_csv(file) if file.endswith('.csv') else pd.read_excel(file)
        df = df[['Rider ID', 'Rider → Rider Name', 'Rider → Phone', 'Rider → Team Name']].dropna()
        rider_data = pd.concat([rider_data, df], ignore_index=True)
    except Exception as e:
        print(f"Error reading {file}: {e}")

# Count how many times each Rider ID appears
rider_counts = rider_data['Rider ID'].value_counts()
rider_data['Rider - total count'] = rider_data['Rider ID'].map(rider_counts)

# Group by team and sum rider appearances
team_counts = rider_data.groupby('Rider → Team Name')['Rider - total count'].sum().sort_values(ascending=False)

# Plot line graph
plt.figure(figsize=(14, 7))
sns.set(style="whitegrid")
sns.lineplot(
    x=team_counts.index,
    y=team_counts.values,
    marker='o',
    linestyle='-',
    palette='husl'
)

plt.title("Total Rider Appearances per Team", fontsize=16)
plt.xlabel("Team Name", fontsize=12)
plt.ylabel("Total Appearances", fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
graph_filename = "team_rider_appearance_graph.png"
plt.savefig(graph_filename, dpi=300)
plt.close()

# Find highest appearing riders
top_riders = rider_data.sort_values(by='Rider - total count', ascending=False).drop_duplicates('Rider ID')

# Prepare output folder
today_str = datetime.now().strftime("%Y-%m-%d")
base_output = f"Fake_offender_data_{today_str}"
output_dir = os.path.join(base_dir, base_output)
suffix = 1
while os.path.exists(output_dir):
    output_dir = os.path.join(base_dir, f"{base_output}-{suffix}")
    suffix += 1
os.makedirs(output_dir)

# Save to Excel
output_file = os.path.join(output_dir, os.path.basename(output_dir) + ".xlsx")
top_riders.to_excel(output_file, index=False)

# Add graph to Excel
wb = load_workbook(output_file)
ws = wb.active
img = XLImage(graph_filename)
img.width = 800
img.height = 400
ws.add_image(img, "G2")
wb.save(output_file)

print(f"✅ Done! File saved to: {output_file}")
