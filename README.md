# ironic-provisioning-lab

Bare-metal provisioning pipeline built on OpenStack Ironic patterns.

## What this covers

- **PXE/iPXE boot** — DHCP-driven network boot chain for unattended OS deployment
- **IPMI/Redfish hardware control** — power management, sensor polling, console access
- **Ironic Python Agent (IPA)** — node inspection, in-band provisioning, hardware inventory
- **Automated server lifecycle** — enroll → inspect → provision → clean → available

## Architecture

```
Ironic API → Conductor → IPA (on node)
              │
              ├── IPMI/Redfish (OOB management)
              ├── PXE/iPXE (boot chain)
              └── Swift/HTTP (image store)
```

## Based on

Production patterns from operating 100+ physical nodes in a private cloud environment.
Includes lessons learned from at-scale bare-metal operations: race conditions in
concurrent provisioning, IPMI quirks across hardware vendors, IPA failure modes.

## Status

Work in progress — extracting patterns from production into documented, reproducible examples.

