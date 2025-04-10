import os
import requests
import pandas as pd
import datetime
import time

def get_unique_folder():
    """Create a unique folder for storing images with date suffix."""
    today = datetime.date.today().strftime("%Y-%m-%d")
    base_folder = f"fake_attendance_image_{today}"
    folder = base_folder
    counter = 1

    while os.path.exists(folder):
        folder = f"{base_folder}-{counter}"
        counter += 1

    os.makedirs(folder)
    return folder

def download_images_from_excel(file_path):
    """Download images from 'Image URL' column and save with 'Rider ID' as filename."""
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    # Ensure required columns exist
    if "Image URL" not in df.columns or "Rider ID" not in df.columns:
        print(f"❌ Columns 'Image URL' or 'Rider ID' not found in the file!")
        return

    save_folder = get_unique_folder()
    total_rows = len(df)
    if total_rows == 0:
        print("⚠️ No data found in the file.")
        return

    print(f"📂 Saving images to: {save_folder}")

    for i, row in df.iterrows():
        try:
            image_url = str(row["Image URL"]).strip()
            rider_id = str(row["Rider ID"]).strip()

            if not image_url or not rider_id or image_url.lower() == 'nan':
                continue  # Skip rows with missing data

            image_path = os.path.join(save_folder, f"{rider_id}.jpg")

            response = requests.get(image_url, stream=True, timeout=10)
            if response.status_code == 200:
                with open(image_path, "wb") as img_file:
                    img_file.write(response.content)

            # Update the loading progress
            progress = int(((i + 1) / total_rows) * 100)
            print(f"\r⏳ Downloading... {progress}%", end="", flush=True)

        except Exception as e:
            print(f"\n❌ Error downloading image for Rider ID {rider_id}: {e}")

    print("\n✅ Download completed!")

if __name__ == "__main__":
    file_path = input("📂 Enter the Excel file path: ").strip()

    if os.path.exists(file_path):
        download_images_from_excel(file_path)
    else:
        print("❌ File not found! Please enter a valid path.")
