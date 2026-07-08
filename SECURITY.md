# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within **Relay**, please send an email to sdusane4@gmail.com. All reports will be promptly addressed.

**Please include the following in your report:**

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if applicable)
- Your contact information for follow-up

## Response Timeline

- **Acknowledgment:** Within 48 hours of report submission
- **Initial Assessment:** Within 72 hours
- **Fix Deployment:** Within 7 days for confirmed vulnerabilities

## Security Update Process

1. Vulnerability reports are triaged and prioritized
2. A fix is developed and tested in a private branch
3. Security patch is released as a minor or patch version bump
4. Affected users are notified via release notes
5. CVE is requested if applicable

## Security-Related Configuration

- Relay nodes authenticate peers using mTLS certificates
- Message payloads are encrypted in transit using TLS 1.3
- Forward secrecy is ensured through ephemeral key exchange
- Node identity is anchored to a certificate authority
- Circuit breakers protect against cascade failures from compromised nodes

## Known Security Gaps

- Message replay attacks are mitigated only by timestamp-based windowing
- Node certificate revocation relies on periodic CRL checks rather than OCSP
- Load balancing does not account for node trust scores
