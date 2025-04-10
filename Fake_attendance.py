import os
import time
import shutil
import pandas as pd
import requests
import cv2
import numpy as np
from datetime import datetime

def create_unique_folder(base_name):
    counter = 0
    folder_name = base_name
    while os.path.exists(folder_name):
        counter += 1
        folder_name = f"{base_name}-{counter}"
    os.makedirs(folder_name)
    return folder_name

def display_loading(duration=10):
    steps = 100
    for i in range(steps + 1):
        time.sleep(duration / steps)  # Adjust time based on estimated process duration
        print(f"Processing: {i}%", end="\r")

def download_image(image_url):
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            return cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"Error downloading image: {e}")
    return None

def is_fake_image(image):
    if image is None:
        return False
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    return np.mean(edges) < 10

def detect_fake_attendance(file_path):
    df = pd.read_excel(file_path)
    total_records = len(df)
    fake_attendance_records = []
    
    for index, row in df.iterrows():
        image_url = row.get("Image URL", "")
        if image_url:
            image = download_image(image_url)
            if is_fake_image(image):
                fake_attendance_records.append(row)
        
        progress = int((index + 1) / total_records * 100)
        print(f"Processing: {progress}%", end="\r")
    
    if fake_attendance_records:
        fake_df = pd.DataFrame(fake_attendance_records)
        today_date = datetime.now().strftime('%Y-%m-%d')
        folder_name = create_unique_folder(f"fake_attendance_{today_date}")
        output_file = os.path.join(folder_name, f"fake_rider_attendance_{today_date}.xlsx")
        fake_df.to_excel(output_file, index=False)
        print(f"\nFake attendance records saved in: {output_file}")
    else:
        print("\nNo fake attendance detected.")

if __name__ == "__main__":
    input_file = input("Enter the path of the attendance .xlsx file: ")
    if os.path.exists(input_file) and input_file.endswith('.xlsx'):
        print("Starting processing...\n")
        display_loading(duration=5)  # Simulated loading time
        detect_fake_attendance(input_file)
        print("\nProcessing complete!")
    else:
        print("Invalid file. Please provide a valid .xlsx file.")
