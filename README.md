# QuantumRelay

> A browser-native, post-quantum secure messaging platform that combines ML-KEM (Kyber), ML-DSA (Dilithium), forward secrecy, zero-knowledge architecture, and latency-aware handshakes to achieve practical quantum-resistant communication without sacrificing user experience.

---

## Overview

QuantumRelay is an experimental secure communication platform designed to explore the practical deployment of Post-Quantum Cryptography (PQC) in real-time messaging systems.

Unlike traditional messaging applications that rely on RSA, ECC, or ECDH, QuantumRelay leverages NIST-standardized post-quantum cryptographic algorithms to establish secure communication channels that remain resistant to future quantum-computing attacks.

The project focuses on solving a key deployment challenge:

> How can post-quantum cryptography be integrated into real-time communication systems without introducing noticeable latency for users?

---

## Key Features

### Post-Quantum Authentication

* ML-DSA-65 (Dilithium)
* Public key authentication
* Protection against Man-in-the-Middle attacks

### Post-Quantum Key Exchange

* ML-KEM-768 (Kyber)
* Quantum-resistant shared secret generation
* Session-based secure communication

### End-to-End Encryption

* AES-256-GCM
* Confidentiality
* Integrity protection
* Authenticated encryption

### Forward Secrecy

* HKDF-SHA256 ratcheting
* Session key rotation every 5 minutes
* Historical message protection

### Zero-Knowledge Architecture

Server can never access:

* Plaintext messages
* Encryption keys
* User secrets

### Anonymous Communication

No requirement for:

* Accounts
* Email addresses
* Phone numbers
* Persistent identities

### Web Worker Isolation

Cryptographic operations run inside dedicated browser workers.

Benefits:

* Reduced attack surface
* Improved responsiveness
* Better key isolation

### Hybrid Security Modes

#### Pure PQC

```text
ML-DSA
+
ML-KEM
```

#### Hybrid

```text
ML-DSA + ECDSA
ML-KEM + ECDH
```

#### Classical Fallback

```text
ECDSA
+
ECDH
```

---

## Research Contribution

QuantumRelay does not introduce a new cryptographic algorithm.

Instead, its contribution lies in practical deployment engineering:

### Latency-Aware PQC Handshake

Traditional Approach:

```text
Handshake
    ↓
Authentication
    ↓
Open Chat
```

QuantumRelay Approach:

```text
Open Chat Interface
        ↓
Run PQC Handshake Asynchronously
        ↓
Establish Secure Session
```

This design reduces perceived startup delay and improves usability while maintaining strong security guarantees.

---

## Security Architecture

```text
Participant A
      │
      ▼
ML-DSA Authentication
      │
      ▼
ML-KEM Key Exchange
      │
      ▼
Shared Secret
      │
      ▼
HKDF Key Derivation
      │
      ▼
AES-256-GCM Encryption
      │
      ▼
Zero-Knowledge Relay Server
      │
      ▼
Participant B
```

---

## Technology Stack

### Frontend

* React
* TypeScript
* Web Workers

### Backend

* FastAPI
* WebSockets

### Cryptography

* liboqs-js
* WebAssembly (WASM)
* ML-KEM-768 (Kyber)
* ML-DSA-65 (Dilithium)
* AES-256-GCM
* HKDF-SHA256

### Infrastructure

* Docker
* Nginx
* Linux

---

## Project Structure

```text
QuantumRelay/
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── workers/
│   └── crypto/
│
├── backend/
│   ├── api/
│   ├── websocket/
│   ├── relay/
│   └── security/
│
├── docs/
│
├── research/
│
├── benchmarks/
│
└── README.md
```

---

## Security Goals

### Confidentiality

Only intended participants can read messages.

### Integrity

Messages cannot be modified undetected.

### Authentication

Participants verify exchanged public keys.

### Forward Secrecy

Past communications remain protected even if a session key is compromised.

### Quantum Resistance

Communication remains secure against attacks from future quantum computers.

---

## Performance Goals

| Metric            | Target      |
| ----------------- | ----------- |
| Handshake Latency | < 200 ms    |
| Message Delivery  | < 100 ms    |
| Key Rotation      | Every 5 min |
| Availability      | > 99%       |

---

## Current Status

### Implemented

* Project architecture
* PQC design specification
* Security model
* Research framework

### In Progress

* Browser integration
* PQC handshake implementation
* WebSocket relay layer
* Benchmarking framework

### Planned

* Experimental evaluation
* Hybrid mode testing
* Performance measurements
* Research paper submission

---

## Research Roadmap

### Phase 1

* Core chat system
* PQC integration
* Authentication workflow

### Phase 2

* Forward secrecy implementation
* Web Worker isolation
* Hybrid cryptography mode

### Phase 3

* Benchmarking
* Experimental analysis
* Comparative evaluation

### Phase 4

* Academic publication
* Open-source release
* Production hardening

---

## Future Enhancements

* Group messaging
* Secure file transfer
* Decentralized relay nodes
* Mobile clients
* PQC algorithm upgrades
* Multi-device support

---

## Disclaimer

QuantumRelay is a research and educational project intended to explore practical deployment challenges of Post-Quantum Cryptography.

The platform should not be considered production-ready until extensive security auditing, benchmarking, and validation have been completed.

---

## Author

**Adwith Satya**

B.Tech Cybersecurity

Research Interests:

* Post-Quantum Cryptography
* Secure Communication Systems
* Browser Security
* Applied Cryptography
* Privacy Engineering

---

## License

MIT License

---

⭐ If you find this project interesting, consider starring the repository and following its research progress.
