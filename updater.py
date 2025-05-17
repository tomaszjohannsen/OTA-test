# updater.py
# downloads an update for main.py if available.
# use install_update_if_available in a try clause.
# install_update_if_available returns True if an update was downloaded and installed.
# in most cases that should be followed by calling machine.reset()

import os
import urequests
import re

TEMP_FILE = "ota-update.temp.py"
MAX_SIZE = 100 * 1024


def download_update(ota_url):
    """Downloads the new main.py to a temporary file. Aborts if size exceeds MAX_SIZE."""
    print(f'trying to download {ota_url}')
    try:
        response = urequests.get(ota_url, stream=True)
        if response.status_code == 200:
            total_size = 0
            with open(TEMP_FILE, 'wb') as file:
                while True:
                    chunk = response.raw.read(1024)
                    if not chunk:
                        break

                    # Update total size and check if limit exceeded
                    total_size += len(chunk)
                    if total_size > MAX_SIZE:
                        print("Error: File size exceeds 50KB limit")
                        file.close()
                        try:
                            os.remove(TEMP_FILE)
                        except:
                            pass
                        return False

                    file.write(chunk)
            return True, "Downloaded"
        else:
            return False, f"Failed to download file. Status code: {response.status_code}"

    except Exception as e:
        return False, f"Error during update download: {e}"
    finally:
        if 'response' in locals():
            response.close()


def install_update():
    """Installs the downloaded update by replacing main.py."""
    print("Installing update...")
    try:
        # Remove old main.py (optional but good practice)
        try:
            os.remove("main.py")
            print("Removed old main.py")
        except OSError:
            print("No existing main.py to remove.")  # File might not exist yet

        # Rename temp file to main.py
        os.rename(TEMP_FILE, "main.py")
        print("Renamed temporary file to main.py")

        # Clean up the temporary file if rename somehow failed (unlikely but safe)
        try:
            os.remove(TEMP_FILE)
        except OSError:
            pass  # File already renamed or didn't exist

        print("Update installed successfully.")
        return True, "Update installed"
    except Exception as e:
        # Attempt to clean up temp file if installation failed
        try:
            os.remove(TEMP_FILE)
        except OSError:
            pass
        return False, f"Error during update installation: {e}"


def compare_versions(current, latest):
    """Compares version strings (simple string comparison).
       Assumes versions are like X.Y.Z.
       Returns True if latest > current.
    """
    if not current or not latest:
        return False

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
        return False  # Versions are equal
    except ValueError:
        print("Warning: Could not parse version strings for comparison.")
        # Fallback to simple string comparison if number parsing fails
        return latest > current


def sanitize_update(file, expected_version):
    try:
        file_size = os.stat(file)[6]  # index 6 is st_size
        if file_size > MAX_SIZE:
            return False, f"File size {file_size} bytes exceeds maximum allowed size"

        # Check for the required patterns line by line
        has_main_check = False
        has_version = False

        with open(file, 'r') as f:
            for line in f:
                # Check for __version__ string
                if '__version__' in line:
                    print('found __version__')
                    has_version = True

                # Strip whitespace but keep initial indentation
                stripped = line.rstrip()
                # Check if the line starts with whitespace (indented)
                if stripped and not stripped[0].isspace():
                    # Remove all whitespace between characters for comparison
                    condensed = re.sub(r'\s+', ' ', stripped).strip()
                    if condensed == "if __name__ == '__main__':" or condensed == 'if __name__ == "__main__":':
                        print('found __main__')
                        has_main_check = True

        print('has required strings?', has_version, has_main_check)

        if not has_main_check:
            return False, "Missing '__main__' check"

        if not has_version:
            return False, "Missing '__version__' string"

        print('proceeding to load the file in a namespace')
        # For syntax validation and version check, use exec instead of importlib
        # Create a temporary namespace for executing the module
        namespace = {}

        try:
            # Read the file content for exec
            with open(file, 'r') as f:
                code = f.read()

            # Execute the code in the isolated namespace
            exec(code, namespace)

            # Check if __version__ is defined and matches
            if '__version__' not in namespace:
                return False, "'__version__' attribute not defined in the module"

            if namespace['__version__'] != expected_version:
                return False, f"Version mismatch: expected {expected_version}, got {namespace['__version__']}"

        except SyntaxError as e:
            return False, f"Invalid Python syntax: {str(e)}"

        return True, "success"

    except Exception as e:
        print(f"Error during validation: {str(e)}")
        return False, f"Error during validation: {str(e)}"


def install_update_if_available(current_version, ota_version, ota_url):
    """Checks for and performs an OTA update if available."""
    print("Starting OTA update check...")

    if compare_versions(current_version, ota_version):
        print(f"New version {ota_version} available. Current version {current_version}.")
        download_success, download_message = download_update(ota_url)
        if not download_success:
            raise Exception(download_message)
        sanitize_success, sanitize_message = sanitize_update(TEMP_FILE, ota_version)
        if not sanitize_success:
            raise Exception(sanitize_message)
        install_success, install_message = install_update()
        if not install_success:
            raise Exception(install_message)
        return True
    else:
        return False
