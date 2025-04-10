import os
import cv2
import requests
import numpy as np
import pandas as pd
import time
from datetime import datetime

def is_fake_image(image_url):
    """Determines if an image is fake based on blurriness."""
    try:
        if pd.isna(image_url) or not isinstance(image_url, str) or not image_url.startswith("http"):
            return False  # Invalid URL
        
        response = requests.get(image_url, stream=True, timeout=5)
        if response.status_code != 200:
            return False  # Unable to fetch image
        
        image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if image is None:
            return False  # Unable to decode image

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

#       gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#       laplacian_var = cv2.Laplacian(gray, cv2.CV_64F, ksize=3).var()
        
        return laplacian_var < 50  # Threshold for blurriness
    
    except Exception as e:
        return False  # Ignore errors and continue

def process_attendance(file_path):
    """Processes the attendance Excel file to detect fake images."""
    try:
        start_time = time.time()  # Start timer

        df = pd.read_excel(file_path)
        
        # Standardizing column names
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

        for index, row in df.iterrows():
            rider_id = row['Rider ID']
            rider_name = row.get('Rider Name', 'Unknown')
            image_url = row.get('Image URL', None)

            if is_fake_image(image_url):
                fake_records.append(row.to_dict())

            # Print progress every 100 riders
            if (index + 1) % 100 == 0:
                print(f"📌 Processed {index + 1}/{len(df)} riders...")

        if fake_records:
            save_fake_attendance(fake_records)
            print(f"✅ Fake attendance detected. File saved successfully!")
        else:
            print("✅ No fake images detected.")

        end_time = time.time()  # End timer
        print(f"⏳ Total processing time: {round(end_time - start_time, 2)} seconds.")
    
    except Exception as e:
        print(f"Error: {e}")

def save_fake_attendance(fake_records):
    """Saves detected fake attendance records to an Excel file."""
    try:
        output_dir = "fake_attendance_reports"
        os.makedirs(output_dir, exist_ok=True)
        
        file_name = f"fake_rider_attendance_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        output_path = os.path.join(output_dir, file_name)

        df_fake = pd.DataFrame(fake_records)
        df_fake.to_excel(output_path, index=False)

        print(f"📂 Report saved: {output_path}")
    
    except Exception as e:
        print(f"Error saving fake attendance file: {e}")

if __name__ == "__main__":
    file_path = input("Enter the path of the attendance Excel file (.xlsx only): ").strip()
    process_attendance(file_path)
