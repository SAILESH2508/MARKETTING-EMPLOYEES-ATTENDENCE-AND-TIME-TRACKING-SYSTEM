import requests
import os

urls = [
    "https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.24.1-cp311-cp311-win_amd64.whl",
    "https://github.com/Murtaza-Saeed/dlib-waheels/raw/main/dlib-19.24.1-cp311-cp311-win_amd64.whl" 
]

filename = "dlib-19.24.1-cp311-cp311-win_amd64.whl"

for url in urls:
    print(f"Trying to download from {url}...")
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Successfully downloaded {filename}")
            if os.path.getsize(filename) > 10000: # Simple check to ensure it's not a tiny error page
                print("File seems valid.")
                exit(0)
            else:
                print("File too small, probably invalid.")
        else:
            print(f"Failed with status code: {response.status_code}")
    except Exception as e:
        print(f"Error downloading: {e}")

print("Could not download dlib wheel from any source.")
exit(1)
