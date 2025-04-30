import os

# Generate a 24-byte secret key
secret_key = os.urandom(24)

# Convert it to a hexadecimal string (to make it readable)
hex_secret_key = secret_key.hex()

# Print the key to use or save for later
print("Generated Secret Key:", hex_secret_key)
