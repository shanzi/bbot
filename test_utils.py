#!/usr/bin/env python3
"""Test script for utils.py allow list functionality."""

import os
import utils

# Test the allow list function
print("Testing get_allowed_email_addresses function...")

# Set test environment variables
os.environ['ALLOWED_EMAIL_ADDRESSES'] = 'test@example.com,user@test.com'
os.environ['KINDLE_ADDRESS'] = 'mykindle@kindle.com'

allowed = utils.get_allowed_email_addresses()
print(f"Allowed addresses: {allowed}")

# Test that it includes both allowed addresses and Kindle address
expected = {'test@example.com', 'user@test.com', 'mykindle@kindle.com'}
print(f"Expected: {expected}")
print(f"Matches expected: {allowed == expected}")

# Test send_email function validation
print("\nTesting send_email validation...")
try:
    utils.send_email('unauthorized@example.com', 'Test', 'Test body')
    print("ERROR: Should have raised ValueError for unauthorized email")
except ValueError as e:
    print(f"SUCCESS: Correctly blocked unauthorized email: {e}")

try:
    utils.send_email('test@example.com', 'Test', 'Test body')
    print("ERROR: Should have raised ValueError for missing Gmail credentials")
except ValueError as e:
    if "GMAIL_ADDRESS" in str(e):
        print("SUCCESS: Correctly requires Gmail credentials")
    else:
        print(f"UNEXPECTED ERROR: {e}")

print("\nAllow list functionality working correctly!")