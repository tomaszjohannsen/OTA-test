# updater.py
# version 3.0 has sanity check to verify proper "main" name protection, python lib loading and version number verification
# version 2.0 using 3 parameter interface and assuming network is connected.
# use this in a try catch structure clause, in case wifi connection breaks, etc.

import uos
import urequests
import network
import time
import machine

# --- Configuration ---
TEMP_MAIN_PY = "maintmp.py"
# --- End Configuration ---


def download_update(ota_url):
    """Downloads the new main.py to a temporary file."""
   
    try:
        uos.remove(TEMP_MAIN_PY)
        print(f"Removed old {TEMP_MAIN_PY}")
    except OSError:
        print(f"No existing {TEMP_MAIN_PY} to remove.") # File might not exist yet
   
   
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

def check_main_guard():
    pattern = "if__name__==\"__main__\":"  # No whitespace version of what we're looking for
   
    try:
        with open(TEMP_MAIN_PY, 'r') as file:
            for line in file:
                # Remove all whitespace and compare
                clean_line = ''.join(line.split())
                if clean_line == pattern:
                    return True
           
        # If we get here, we didn't find the pattern
        return False
    except OSError as e:
        print(f"Error reading {filename}: {e}")
        return False

def check_version(expected_version):
    module_name = TEMP_MAIN_PY
    module_name = module_name.split('.')[0]
    print(f"Checking version is module {module_name}")
    try:
        # Import the sys module for manipulating the import system
        import sys
       
        # Remove the module from sys.modules if it was previously imported
        # This ensures we get a fresh import with the latest version
        if module_name in sys.modules:
            del sys.modules[module_name]
       
        # Import the module
        module = __import__(module_name)
       
        # Check if __version__ exists
        if hasattr(module, '__version__'):
            version = module.__version__
            print(f"Module {module_name} version: {version}")
           
            return version == expected_version
        else:
            print(f"Module {module_name} has no __version__ attribute")
            return False
    except ImportError as e:
        print(f"Error importing {module_name}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def sanity_check(ota_version):
    """Verifies a few things about the downloaded file before installing."""
    print("Doing sanity checks...")

    # First check the main guard line
    if check_main_guard():
        print("Check guard for 'main.py' passed.")
        # Second, check that it loads as a python library. temp = importlib.import_module('main-temp') Then you can check temp.__version__ to confirm.
        if check_version(ota_version):
            print("File version matches ota version.")
            return True
        else:
            print("Version in file does not match latest ota version.")
            return False                
    else:
        print("Could not find __main__ guard check in latest version.")
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


def update_if_available(current_version, ota_version, ota_url):
    """Checks for and performs an OTA update if available."""
    print("Starting OTA update check...")

    if compare_versions(current_version, ota_version):
        print(f"New version {ota_version} available. Current version {current_version}.")
        if download_update(ota_url):
            if sanity_check(ota_version):
                if install_update():
                    print("Update successful! Rebooting to apply...")
                    # Small delay to let print messages flush
                    time.sleep(2)
                    machine.reset() # Reboot the device
                else:
                    print("Update installation failed.")
            else:
                print("Sanity check failed.")
        else:
            print("Update download failed.")
           
        return True # Signifies that an attempt was made or completed
    else:
        print("Device is already running the latest version.")
        return False # No update needed or available


