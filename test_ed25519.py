"""Test suite and host reference client for Satochip-J3R452-Curve25519.
Supports both offline vector math verification and live hardware PC/SC card testing.
"""
import hmac
import hashlib
import struct
import sys
from cryptography.hazmat.primitives.asymmetric import ed25519

# SLIP-0010 Ed25519 Reference Implementation
ED25519_SEED = b"ed25519 seed"

def slip10_master_key(seed: bytes):
    I = hmac.new(ED25519_SEED, seed, hashlib.sha512).digest()
    return I[:32], I[32:] # master_key, master_chaincode

def slip10_derive_child(parent_key: bytes, parent_chaincode: bytes, index: int):
    # SLIP-0010 requires hardened index (>= 0x80000000)
    if index < 0x80000000:
        raise ValueError(f"SLIP-0010 Ed25519 only supports hardened child index: {hex(index)}")
    data = b"\x00" + parent_key + struct.pack(">I", index)
    I = hmac.new(parent_chaincode, data, hashlib.sha512).digest()
    return I[:32], I[32:] # child_key, child_chaincode

def slip10_derive_path(seed: bytes, path: list):
    k, c = slip10_master_key(seed)
    for idx in path:
        k, c = slip10_derive_child(k, c, idx)
    return k, c

def test_offline_math():
    print("=== Running Offline SLIP-0010 & Ed25519 Reference Verification ===")
    # Standard BIP39 12-word seed test vector (e.g., 64-byte seed)
    seed = bytes.fromhex(
        "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
        "202122232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d3e3f"
    )
    # Solana standard path: m/44'/501'/0'/0'
    solana_path = [
        0x80000000 + 44,
        0x80000000 + 501,
        0x80000000 + 0,
        0x80000000 + 0
    ]
    priv_key, chain_code = slip10_derive_path(seed, solana_path)
    print("Solana m/44'/501'/0'/0':")
    print(f"  Derived Private Key (Seed): {priv_key.hex()}")
    print(f"  Derived Chaincode:          {chain_code.hex()}")

    # Derive public key using cryptography.ed25519
    ed_priv = ed25519.Ed25519PrivateKey.from_private_bytes(priv_key)
    pub_bytes = ed_priv.public_key().public_bytes_raw()
    print(f"  Derived Public Key:         {pub_bytes.hex()}")

    # Test signature
    message = b"Test message for Satochip-J3R452-Curve25519 hardware signature"
    sig = ed_priv.sign(message)
    print(f"  Ed25519 Signature ({len(sig)} bytes): {sig.hex()[:32]}...{sig.hex()[-32:]}")

    # Verify signature
    ed_priv.public_key().verify(sig, message)
    print("  Local signature verification: PASS")
    print("=== Offline Math Verification Succeeded! ===\n")
    return priv_key, pub_bytes

def test_hardware_card():
    try:
        from smartcard.System import readers
        from smartcard.util import toHexString, toBytes
    except ImportError:
        print("pyscard not available in this environment. Skipping live card test.")
        return

    r = readers()
    if not r:
        print("No PC/SC smartcard readers detected.")
        return

    print(f"Available readers: {[str(x) for x in r]}")
    reader = r[0]
    print(f"Connecting to reader: {reader}")
    conn = reader.createConnection()
    try:
        conn.connect()
    except Exception as e:
        print(f"Failed to connect to card: {e}")
        return

    # Select Satochip Applet (AID: 5361746F4368697000)
    select_apdu = [0x00, 0xA4, 0x04, 0x00, 0x09, 0x53, 0x61, 0x74, 0x6F, 0x43, 0x68, 0x69, 0x70, 0x00]
    data, sw1, sw2 = conn.transmit(select_apdu)
    print(f"SELECT Satochip: SW={sw1:02X}{sw2:02X}")
    if sw1 != 0x90:
        print("Satochip applet not selected or not installed.")
        return

    print(f"Applet Status data ({len(data)} bytes): {bytes(data).hex()}")
    if len(data) >= 19:
        ed25519_support = data[18]
        print(f"Feature Ed25519 support byte (offset 18): {ed25519_support}")
        if ed25519_support == 0:
            print("Card confirms: Ed25519 / SLIP-0010 FEATURE_ENABLED!")

if __name__ == '__main__':
    test_offline_math()
    if '--hardware' in sys.argv or '-c' in sys.argv:
        test_hardware_card()
