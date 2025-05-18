# OTA updater for MicroPython

The updater checks whether there is an update available for main.py.
If so, it does a few sanity checks and then downloads the update.
Checks include: 
 * The OTA version shouldn't have syntax errors
 * The OTA version cannot exceed 100 KB
 * The OTA version must set its `__version__` and it must match the version that's expected
 * The OTA version must have code in a block that checks `if __name__ == 'main':`

Usage:
```Python
    import updater
    import machine
    import time
    
    # Assuming the device is already connected to WiFi
    
    try:
        if updater.install_update_if_available(current_version, ota_version, ota_url):
            print("Update successful! Rebooting to apply...")
            time.sleep(3)
            machine.reset() # Reboot the device
    except Exception as e:
        print(f'Updater error: {e}')

```