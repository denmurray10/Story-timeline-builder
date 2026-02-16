import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

token = os.getenv("FIGMA_ACCESS_TOKEN")
file_key = "ZMRhKSrEDRDiMp2ul5MlgI"
node_ids = "32:2"

if not token:
    print("Error: FIGMA_ACCESS_TOKEN not found in environment variables.")
    exit(1)

headers = {
    "X-Figma-Token": token
}

# Get node data
url = f"https://api.figma.com/v1/files/{file_key}/nodes?ids={node_ids}"
try:
    response = requests.get(url, headers=headers, timeout=10)
    print("Node Status Code:", response.status_code)
    if response.status_code == 200:
        data = response.json()
        print("Node data fetched")
    else:
        print(response.text)
except Exception as e:
    print("Error fetching node data:", e)

# Get image URL
url = f"https://api.figma.com/v1/images/{file_key}?ids={node_ids}&format=png"
try:
    response = requests.get(url, headers=headers, timeout=10)
    print("Image URL Status Code:", response.status_code)
    if response.status_code == 200:
        image_url = response.json().get("images", {}).get(node_ids)
        print("Image URL:", image_url)
        if image_url:
            img_data = requests.get(image_url, timeout=10).content
            with open("figma_design.png", "wb") as handler:
                handler.write(img_data)
            print("Image saved as figma_design.png")
    else:
        print(response.text)
except Exception as e:
    print("Error fetching image:", e)
