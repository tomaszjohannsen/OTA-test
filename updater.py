# updater.py
# version 2.1 using chunks
# use this in a try catch structure clause, in case wifi connection breaks, etc.

import uos
import urequests
import network
import time
import machine

# --- Configuration ---
TEMP_MAIN_PY = "main.py.tmp"
# --- End Configuration ---


def download_update(ota_url):
    """Downloads the new main.py to a temporary file."""
   
    try:
        # Make the HTTP request
        response = urequests.get(ota_url, stream=True)
       
        # Check if the request was successful
        if response.status_code == 200:
            # Open the destination file for writing in binary mode
            with open(TEMP_MAIN_PY, 'wb') as file:
                # Read and write the file in chunks
                while True:
                    chunk = response.raw.read(1024)
                    if not chunk:
                        break
                    file.write(chunk)
           
            print(f"Download successful. Saved to {TEMP_MAIN_PY}")
            return True
        else:
            print(f"Failed to download file. Status code: {response.status_code}")
            return False
           
    except Exception as e:
        print(f"Error during update download: {e}")
        raise
    finally:
        # Make sure to close the response
        if 'response' in locals():
            response.close()


def install_update():
    """Installs the downloaded update by replacing main.py."""
    print("Installing update...")
    try:
        # Remove old main.py (optional but good practice)
        try:
            uos.remove("main.py")
            print("Removed old main.py")
        except OSError:
            print("No existing main.py to remove.") # File might not exist yet

        # Rename temp file to main.py
        uos.rename(TEMP_MAIN_PY, "main.py")
        print("Renamed temporary file to main.py")

        # Clean up the temporary file if rename somehow failed (unlikely but safe)
        try:
             uos.remove(TEMP_MAIN_PY)
        except OSError:
             pass # File already renamed or didn't exist

        print("Update installed successfully.")
        return True
    except Exception as e:
        print(f"Error during update installation: {e}")
        # Attempt to clean up temp file if installation failed
        try:
            uos.remove(TEMP_MAIN_PY)
        except OSError:
            pass
        return False

def compare_versions(current, latest):
    """Compares version strings (simple string comparison).
       Assumes versions are like X.Y.Z.
       Returns True if latest > current.
    """
    if not current or not latest:
        return False # Cannot compare

    # Simple split and compare parts
    try:
        cur_parts = [int(x) for x in current.split('.')]
        lat_parts = [int(x) for x in latest.split('.')]
        # Pad the shorter version with zeros
        max_len = max(len(cur_parts), len(lat_parts))
        cur_parts += [0] * (max_len - len(cur_parts))
        lat_parts += [0] * (max_len - len(lat_parts))

        for i in range(max_len):
            if lat_parts[i] > cur_parts[i]:
                return True
            if lat_parts[i] < cur_parts[i]:
                return False
        return False # Versions are equal
    except ValueError:
        print("Warning: Could not parse version strings for comparison.")
        # Fallback to simple string comparison if number parsing fails
        return latest > current


def update_if_available(current_version, ota_version, ota_url):
    """Checks for and performs an OTA update if available."""
    print("Starting OTA update check...")

    if compare_versions(current_version, ota_version):
        print(f"New version {ota_version} available. Current version {current_version}.")
        if download_update(ota_url):
            if install_update():
                print("Update successful! Rebooting to apply...")
                # Small delay to let print messages flush
                time.sleep(3)
                machine.reset() # Reboot the device
            else:
                print("Update installation failed.")
        else:
            print("Update download failed.")
        return True # Signifies that an attempt was made or completed
    else:
        print("Device is already running the latest version.")
        return False # No update needed or available
