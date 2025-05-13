# --- Application Version ---
# Change this when you make a new version!
__version__ = "1.0.6"
# --- End Application Version ---

import time
import updater # Import the updater module
import machine
import time
import network

# --- Wi-Fi Credentials (can be imported or defined here) ---
# It's often better to define these once in boot.py or a config file
# but for this example, let's pass them to the updater function
# REPLACE WITH YOURS
WIFI_SSID = "Johannet_Guest"
WIFI_PASSWORD = ""
# --- End Wi-Fi Credentials ---

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


print(f"--- Starting Main Application (Version: {__version__}) ---")
# Connect to Wi-Fi on boot
# Note: We don't call the updater here directly.
connect_wifi(WIFI_SSID, WIFI_PASSWORD)


# Define the LED pin
led_pin = 15  #this is for the XIAO ESP32--C6

# Set the LED pin as an output
led = machine.Pin(led_pin, machine.Pin.OUT)

counter = 0
while True:
  counter = counter +1
  print(f"(Version: {__version__}) blinking attempt [{counter}]")
  # Turn the LED on
  led.value(1)
  # Wait for 0.5 seconds
  time.sleep_ms(500)
  # Turn the LED off
  led.value(0)
  # Wait for 0.5 seconds
  time.sleep_ms(500)
  if counter > 5 :
      print("Checking for OTA updates...")
      counter = 0
      update_successful = updater.update_if_available(WIFI_SSID, WIFI_PASSWORD)
      if update_successful:
        # The updater initiated a reboot, this code won't be reached after successful update
        pass
      else:
        # No update or update failed, continue with main application logic
        print("No update available or update failed. Running main application.")
        # --- Your main application logic goes here ---

