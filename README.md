# Satochip-25519-Applet

[![JavaCard](https://img.shields.io/badge/JavaCard-3.0.4%2B-blue.svg)](https://www.oracle.com/java/technologies/javacard.html)
[![Target](https://img.shields.io/badge/Target-NXP%20J3R452%20(P71D600)-green.svg)](https://www.nxp.com)
[![License](https://img.shields.io/badge/License-LGPL--3.0-orange.svg)](LICENSE)
[![Reproducible Build](https://img.shields.io/badge/Build-Reproducible%20(Verified)-brightgreen.svg)](dist/build-manifest.json)

> **Hardware-accelerated Curve25519 (Ed25519 / X25519 / SLIP-0010) JavaCard Applet tailored for NXP JCOP 4.5 / J3R452 smart cards.**  
>
> 🌐 **Language**: [English (Current)](README.md) | [中文 (Chinese)](README.zh-CN.md)  
> 📄 **Technical Whitepaper**: [Specification Whitepaper (English)](SPECIFICATION-Curve25519.en.md) | [开发者协议白皮书 (中文)](SPECIFICATION-Curve25519.zh-CN.md)  
> 🌉 **Companion Host Bridge**: [Satochip-25519-Omni-Bridge](https://github.com/chx818/Satochip-25519-Omni-Bridge)  

---

## Overview

**`Satochip-25519-Applet`** is an open-source JavaCard applet hard fork of [Toporin/SatochipApplet](https://github.com/Toporin/SatochipApplet). It integrates the [`suut/Curve25519-JavaCard`](https://github.com/suut/Curve25519-JavaCard) native cryptographic package (AID `FF00025519`) to unlock native silicon hardware-accelerated **Ed25519 signatures**, **X25519 Diffie-Hellman key agreement**, and **SLIP-0010 multi-chain child key derivation** directly on **NXP J3R452 (P71D600)** secure smart cards.

### Core Architectural Features

* **100% Backward Compatibility (Zero Regression)**: Retains full original Satochip functionality on `secp256k1` (Bitcoin/Ethereum BIP32 derivation, legacy & SegWit transactions, BIP340 Schnorr, Taproot, MuSig2, Liquid). Official desktop clients (Electrum-Satochip, Satomask) function without modification.
* **Dual-Curve Physical Memory Isolation**: The `secp256k1` and `Curve25519` cryptographic subsystems maintain physically isolated states in RAM. Both curves share the unified on-card BIP39 Master Seed, unified PIN authentication, unified retry counters, and unified SecureChannel session.
* **Native Silicon Hardware Acceleration**: Ed25519 signatures execute on the NXP hardware coprocessor with a typical latency of ~220ms.
* **SLIP-0010 Multi-Chain Key Derivation**: Hardened key derivation supporting Solana (501'), TON (607'), Sui (784'), Aptos (637'), Polkadot (354'), and Near (397').
* **Authentikey Certified Public Key Export**: Derivation responses (`0x6B`) return the Montgomery $u$-coordinate certified with a card-internal Authentikey ECDSA signature, allowing host clients to verify card authenticity and birationally recover true Edwards public keys.
* **Strong 2FA Transaction Binding (WYSIWYS)**: Full-message SHA-256 digest binding via HMAC-SHA1 challenge-response ensures end-to-end multi-packet message integrity.

---

> [!NOTE]
> **Project Status**: This is an experimental, community-maintained hardware wallet project. Like the original upstream SatochipApplet, key derivation (BIP32 / SLIP-0010) uses software HMAC-SHA512 combined with on-card hardware SHA-512 acceleration, while Curve25519 (Ed25519 / X25519) operations are fully hardware-accelerated by the native cryptographic coprocessor.

---

## Verified Release Artifacts

The release binary is verified through deterministic dual builds and Oracle Off-Card Verification:

| Artifact | File Path | SHA-256 Hash |
| :--- | :--- | :--- |
| **JavaCard CAP** | [`dist/SatoChip-J3R452-Curve25519.cap`](dist/SatoChip-J3R452-Curve25519.cap) | `9fb7394addd25dbf02d91f805aee04d106a9daa00d3e8df5dca4b6250a8b1dc4` |
| **SHA256 Manifest** | [`dist/SHA256SUMS`](dist/SHA256SUMS) | Cryptographic signature of binary output |
| **Build Audit** | [`dist/build-manifest.json`](dist/build-manifest.json) | Environment, toolchain, and reproducibility records |

---

## Quick Start: Card Deployment

### Prerequisites
* An NXP J3R452 (P71D600) smart card (contact or contactless).
* Any PC/SC-compliant smart card reader.
* Python 3.8+ or Java 17+ (GlobalPlatformPro `gp.jar` is vendored).

### One-Click Installation

To deploy the precompiled release binary onto your physical card:

```powershell
# Windows PowerShell:
.\install.ps1

# If upgrading or replacing an existing Satochip instance:
.\install.ps1 --replace
```

```cmd
:: Windows CMD:
install.bat
```

The installer automatically inspects the card's GlobalPlatform registry. If the `Curve25519` native dependency package (`lib/Curve25519.cap`, AID `FF00025519`) is missing, it installs the library first, followed by the `Satochip-25519-Applet` package (AID `5361746F4368697000`).

---

## Building from Source (Deterministic Build)

### Requirements
* **JDK 17 or newer**, with `JAVA_HOME` configured.
* Git submodules initialized (`sdks/` repository):
  ```bash
  git submodule update --init --recursive
  ```

### Build Command

```powershell
# Reproducible dual build with off-card verifier:
.\build.ps1

# Or using the Gradle wrapper directly:
./gradlew convertJavacard
```

The resulting CAP binary will be validated for byte-for-byte reproducibility against the verified hash: `9fb7394addd25dbf02d91f805aee04d106a9daa00d3e8df5dca4b6250a8b1dc4`.

---

## APDU Command Quick Reference

All Satochip-25519 commands require `CLA = 0xB0` within an established **SecureChannel (AES-128-CBC + HMAC-SHA1)** session.

| INS | Command Name | P1 | P2 | Data Field (Lc) | Response (Le) | Description |
| :---: | :--- | :---: | :---: | :--- | :--- | :--- |
| **`0x3C`** | `INS_GET_STATUS` | `0x00` | `0x00` | None | 19 bytes | Offset 18: `feature_ed25519_policy` (`0x00`: ENABLED) |
| **`0x6B`** | `INS_SLIP10_GET_EXTENDED_KEY` | depth (1..10) | `0x00` / `0x01` / `0x02` | `P2=0/2`: path<br>`P2=1`: path + pubkey | chaincode + public_val + Authentikey sig | SLIP-0010 derivation (`P2=0x02` returns Montgomery $u$) |
| **`0x70`** | `INS_SIGN_ED25519_MESSAGE` | `0xFF` | `0x00` | `[msg_bytes (1..149B)]` | `[sig(64B)]` | Silicon hardware Ed25519 signature + Pairwise verification |
| **`0x68`** | `INS_X25519_KEY_AGREEMENT` | `0xFF` | `0x00` | `[remote_u(32B)]` | `[shared_secret(32B)]` | RFC 7748 Diffie-Hellman key agreement |

For comprehensive technical specifications, packet diagrams, and status word definitions, consult the [Protocol Specification Whitepaper](SPECIFICATION-Curve25519.en.md).

---

## Ecosystem Integration

To connect your hardware card to browser Web3 wallets (**Phantom, Solflare, Tonkeeper, Sui Wallet, Petra, Polkadot.js**), use our companion bridge:

👉 **[Satochip-25519-Omni-Bridge](https://github.com/chx818/Satochip-25519-Omni-Bridge)**: A driverless Windows WebHID virtual Ledger Nano S bridge daemon with automatic multi-chain routing.

---

## License

This project is licensed under the **GNU Lesser General Public License v3.0 (LGPL-3.0)**. See [`LICENSE`](LICENSE) for details.  
Original SatochipApplet copyright (c) Toporin and Satochip S.R.L.
