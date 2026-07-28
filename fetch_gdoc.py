import sys
import requests
import re

def fetch_gdoc(url):
    # Convert Google Doc edit/view URL to export as TXT or HTML
    doc_id_match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if not doc_id_match:
        print("Invalid Google Doc URL")
        sys.exit(1)

    doc_id = doc_id_match.group(1)
    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"

    print(f"Fetching document {doc_id}...")
    try:
        response = requests.get(export_url, timeout=10)
        if response.status_code == 200:
            print("Successfully fetched doc content!")
            print("=" * 60)
            print(response.text[:2000]) # Print first 2000 chars
            print("=" * 60)
            with open("gdoc_content.txt", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("Full content saved to gdoc_content.txt")
        else:
            print(f"Failed to fetch document. Status: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    url = "https://docs.google.com/document/d/101ahg3q2-lgVBICio2ljy24cDbMMVrmk-y8tK7nhyg0/edit"
    fetch_gdoc(url)
