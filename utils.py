import hashlib
import os

def hash_password(password):
    # Generate a random salt
    salt = os.urandom(16)  # 16 bytes of random data
    # Combine the salt and password
    salted_password = salt + password.encode('utf-8')
    # Hash the salted password
    hashed_password = hashlib.sha256(salted_password).hexdigest()
    # Store both the salt and the hash (e.g., salt|hash)
    return salt.hex() + "|" + hashed_password


def verify_password(stored_hash, input_password):
    # Split the stored value into salt and hash
    salt, correct_hash = stored_hash.split('|')
    # Re-create the salted password using the provided input and stored salt
    salted_password = bytes.fromhex(salt) + input_password.encode('utf-8')
    # Hash the input password
    input_hash = hashlib.sha256(salted_password).hexdigest()
    # Compare the hashes
    return input_hash == correct_hash




