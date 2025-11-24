#!/usr/bin/env python3
"""Test script to verify email allow list configuration."""

import utils

allowed = utils.get_allowed_email_addresses()
print("Allowed email addresses:", allowed)
print("Total count:", len(allowed))

# Verify specific addresses
expected_addresses = {
    'yun.er.run@gmail.com',
    'i@chasezhang.me', 
    'i_I9hjPU@kindle.com'  # Kindle address should be auto-included
}

print("\nExpected addresses:", expected_addresses)
print("Configuration is correct:", allowed == expected_addresses)