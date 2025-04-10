import os
from google import genai
from google.genai import types
import cv2
import numpy as np
import requests
import pandas as pd
from datetime import datetime
import time
import json

# Constants
GEMINI_API_KEY = os.environ.get("AIzaSyA6Q4GBLw8LbTa0EsFJVR-B4tgIpN-BQkU")
MODEL_NAME = "gemini-2.0-flash-lite"
BLUR_THRESHOLD = 50  # Adjust as needed
CONFIDENCE_THRESHOLD = 0.7  # Adjust as needed - Minimum confidence for considering a screen detection valid


def is_blurry_image(image_data):
    """Detects if an image is blurry."""
    try:
        image_array = np.asarray(bytearray(image_data), dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if image is None:
            return False
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return laplacian_var < BLUR_THRESHOLD
    except Exception as e:
        print(f"Error during blur detection: {e}")
        return False


def generate_anti_spoofing_response(image_data, mime_type=None):
    """Generates an anti-spoofing response using the Gemini API."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(image_data, mime_type=mime_type or "image/jpeg"),
                types.Part.from_text(text="""Detect if this is a true selfie or an image of a screen showing a selfie."""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
        system_instruction="""You are an anti-spoofing AI agent. Detect if an image is a true selfie or a picture of a screen displaying a selfie. Respond STRICTLY in JSON:
Valid (True Selfie): ```json { "success": true } ```
Invalid (Screen Displaying Selfie): ```json { "success": false, "confidence": [0.0-1.0] } ```
IMPORTANT: Only output the JSON. No other text.""",
    )
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=generate_content_config,
        )
        return response.text
    except Exception as e:
        print(f"Error generating anti-spoofing response: {e}")
        return '{"success": false, "error": "Gemini API error"}'


def is_fake_image(image_url):
    """Combines blur detection and Gemini anti-spoofing to determine if an image is fake."""
    try:
        response = requests.get(image_url, stream=True, timeout=5)
        response.raise_for_status()
        image_data = response.content
        mime_type = response.headers.get('Content-Type')

        if is_blurry_image(image_data):
            print("Image is blurry, likely fake.")
            return True

        gemini_response = generate_anti_spoofing_response(image_data, mime_type=mime_type)
        print(f"Gemini Response: {gemini_response}")

        try:
            json_response = json.loads(gemini_response)
            if not json_response.get("success", True):
                confidence = json_response.get("confidence", 0.0)
                if confidence >= CONFIDENCE_THRESHOLD:
                    print("Gemini detected screen with high confidence.")
                    return True
                else:
                    print(f"Gemini detected a screen, but confidence ({confidence}) is below threshold.")
                    return False
            else:
                print("Gemini determined it is a valid selfie.")
                return False

        except json.JSONDecodeError:
            print("Error decoding Gemini JSON response. Treating as potentially fake.")
            return True

    except requests.exceptions.RequestException as e:
        print(f"Error fetching image: {e}")
        return False

    except Exception as e:
        print(f"Error during processing: {e}")
        return False


def process_attendance(file_path):
    """Processes the attendance Excel file to detect fake images."""
    try:
        start_time = time.time()
        df = pd.read_excel(file_path)
        column_mapping = {'Rider → Rider ID': 'Rider ID', 'Rider → Rider Name': 'Rider Name', 'Image URL': 'Image URL'}
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
            if (index + 1) % 100 == 0:
                print(f"📌 Processed {index + 1}/{len(df)} riders...")
        if fake_records:
            save_fake_attendance(fake_records)
            print(f"✅ Fake attendance detected. File saved successfully!")
        else:
            print("✅ No fake images detected.")
        end_time = time.time()
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