import uos
import urequests
import network
import time
import machine

# --- Configuration ---
# Replace with the base URL of your web server hosting updates
UPDATE_URL_BASE = "https://raw.githubusercontent.com/tomaszjohannsen/OTA-test/main/"
VERSION_FILE_URL = UPDATE_URL_BASE + "version.txt"
MAIN_PY_URL = UPDATE_URL_BASE + "main.py"
TEMP_MAIN_PY = "main.py.tmp"
# --- End Configuration ---

def connect_wifi(ssid, password):
    """Connect to Wi-Fi."""
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print("Connecting to Wi-Fi...")
        sta_if.active(True)
        sta_if.connect(ssid, password)
        # Wait for connection with a timeout
        timeout = 20 # seconds
        while not sta_if.isconnected() and timeout > 0:
            print(".", end="")
            time.sleep(1)
            timeout -= 1
        print()
        if sta_if.isconnected():
            print("Wi-Fi connected:", sta_if.ifconfig())
        else:
            print("Wi-Fi connection failed!")
    else:
        print("Wi-Fi already connected:", sta_if.ifconfig())
    return sta_if.isconnected()

def get_current_version():
    """Reads the current version from main.py."""
    # A simple way: look for a __version__ line in the current main.py file
    current_version = "0.0.0" # Default if not found
    try:
        with open("main.py", "r") as f:
            for line in f:
                if line.strip().startswith("__version__ ="):
                    # Extract the version string
                    version_str = line.split("=")[1].strip().strip('"').strip("'")
                    current_version = version_str
                    break
    except Exception as e:
        print(f"Error reading current version: {e}")
        # If main.py doesn't exist or can't be read, assume base version
        pass
    print(f"Current device version: {current_version}")
    return current_version

def get_latest_version():
    """Fetches the latest version from the server."""
    latest_version = None
    try:
        print(f"Checking latest version from {VERSION_FILE_URL}")
        response = urequests.get(VERSION_FILE_URL)
        if response.status_code == 200:
            latest_version = response.text.strip()
            print(f"Latest server version: {latest_version}")
        else:
            print(f"Error fetching version file. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error during latest version check: {e}")
    return latest_version

def download_update():
    """Downloads the new main.py to a temporary file."""
    print(f"Downloading update from {MAIN_PY_URL}")
    try:
        response = urequests.get(MAIN_PY_URL)
        if response.status_code == 200:
            with open(TEMP_MAIN_PY, "wb") as f:
                f.write(response.content)
            print(f"Download successful. Saved to {TEMP_MAIN_PY}")
            return True
        else:
            print(f"Error downloading update. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error during update download: {e}")
        return False

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


def update_if_available(ssid, password):
    """Checks for and performs an OTA update if available."""
    print("Starting OTA update check...")

    if not connect_wifi(ssid, password):
        print("Skipping update check due to Wi-Fi connection failure.")
        return False

    current_version = get_current_version()
    latest_version = get_latest_version()

    if latest_version is None:
        print("Could not get latest version from server. Skipping update.")
        return False

    if compare_versions(current_version, latest_version):
        print(f"New version {latest_version} available. Current version {current_version}.")
        if download_update():
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


