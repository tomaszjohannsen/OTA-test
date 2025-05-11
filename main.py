"""Main function that prints the version number every 5 seconds."""
import time

# Define a constant version number
VERSION = "1.0.3"

counter = 0
try:
    while True:
        counter += 1
        print(f"[{counter}] my version is {VERSION}")
        time.sleep(5)
except KeyboardInterrupt:
    print("\nProgram terminated by user.")
