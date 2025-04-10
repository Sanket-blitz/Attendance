import os
import cv2
import requests
import numpy as np
import pandas as pd
import time
from datetime import datetime
from tqdm import tqdm

def is_fake_image(image_url):
    """Determines if an image is fake based on multiple factors."""
    try:
        if pd.isna(image_url) or not isinstance(image_url, str) or not image_url.startswith("http"):
            return False, "Invalid URL"
        
        response = requests.get(image_url, stream=True, timeout=5)
        if response.status_code != 200:
            return False, "Image Download Failed"
        
        image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if image is None:
            return False, "Unable to Decode Image"

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        brightness = np.mean(hsv[:, :, 2])
        
        if laplacian_var < 50:
            return True, "Blurry Image"
        if brightness > 200:
            return True, "Screen Glare Detected"
        
        return False, "Live Image"
    except Exception as e:
        return False, f"Processing Error: {str(e)}"

def create_unique_folder(base_name):
    """Creates a unique output folder."""
    counter = 0
    folder_name = base_name
    while os.path.exists(folder_name):
        counter += 1
        folder_name = f"{base_name}-{counter}"
    os.makedirs(folder_name)
    return folder_name

def process_attendance(file_path):
    """Processes the attendance Excel file to detect fake images."""
    try:
        start_time = time.time()
        df = pd.read_excel(file_path)
        
        column_mapping = {
            'Rider → Rider ID': 'Rider ID',
            'Rider → Rider Name': 'Rider Name',
            'Image URL': 'Image URL'
        }
        df.rename(columns=column_mapping, inplace=True)
        
        required_columns = {'Rider ID', 'Rider Name', 'Image URL'}
        if not required_columns.issubset(df.columns):
            print("❌ Error: Required columns missing in the input file.")
            return
        
        fake_records = []
        log_data = []
        
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing", unit="record"):
            rider_id = row['Rider ID']
            image_url = row.get('Image URL', None)
            is_fake, reason = is_fake_image(image_url)
            log_data.append(f"Rider ID: {rider_id} | {reason}")
            
            if is_fake:
                row['Detection Reason'] = reason
                fake_records.append(row.to_dict())
        
        today_date = datetime.now().strftime('%Y-%m-%d')
        folder_name = create_unique_folder(f"fake_attendance_{today_date}")
        
        if fake_records:
            save_fake_attendance(fake_records, folder_name)
            print(f"✅ Fake attendance detected. Report saved in {folder_name}.")
        else:
            print("✅ No fake images detected.")
        
        log_file = os.path.join(folder_name, f"detection_log_{today_date}.txt")
        with open(log_file, "w") as f:
            f.write("\n".join(log_data))
        print(f"📂 Detection log saved: {log_file}")
        
        print(f"⏳ Total processing time: {round(time.time() - start_time, 2)} seconds.")
    except Exception as e:
        print(f"Error: {e}")

def save_fake_attendance(fake_records, folder_name):
    """Saves detected fake attendance records to an Excel file."""
    try:
        file_name = f"fake_rider_attendance_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        output_path = os.path.join(folder_name, file_name)
        df_fake = pd.DataFrame(fake_records)
        df_fake.to_excel(output_path, index=False)
        print(f"📂 Report saved: {output_path}")
    except Exception as e:
        print(f"Error saving fake attendance file: {e}")

if __name__ == "__main__":
    file_path = input("Enter the path of the attendance Excel file (.xlsx only): ").strip()
    process_attendance(file_path)
