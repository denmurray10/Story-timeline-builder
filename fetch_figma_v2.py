import requests
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

token = os.getenv("FIGMA_ACCESS_TOKEN")
file_key = "ZMRhKSrEDRDiMp2ul5MlgI"

def download_node(node_id, filename):
    if not token:
        print("Error: FIGMA_ACCESS_TOKEN not found in environment variables.")
        return False

    headers = {
        "X-Figma-Token": token
    }

    # Get image URL
    url = f"https://api.figma.com/v1/images/{file_key}?ids={node_id}&format=png"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            image_url = response.json().get("images", {}).get(node_id)
            if image_url:
                img_data = requests.get(image_url, timeout=10).content
                with open(filename, "wb") as handler:
                    handler.write(img_data)
                print(f"Image saved as {filename}")
                return True
            else:
                print(f"No image URL found for {node_id}")
        else:
            print(f"Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Error fetching image {node_id}:", e)
    return False

if __name__ == "__main__":
    if len(sys.argv) > 2:
        download_node(sys.argv[1], sys.argv[2])
    else:
        # Default behavior if run without args
        download_node("40:93", "relationship_map_figma.png")
