---
name: apple-screen-time
description: >-
  Apple Screen Time API reference for iOS parental-control and digital-wellbeing apps.
  Use for Family Controls authorization and entitlements, Managed Settings shields,
  Device Activity schedules and extensions, caregiver/child flows, remote approvals,
  or CloudKit synchronization for protected devices.
---

# Apple Screen Time APIs

Source-cited notes for building iOS parental-control and digital-wellbeing apps with
Family Controls, Managed Settings, Device Activity, Screen Time app extensions, and
CloudKit. Reuse these notes before fetching Apple documentation again; re-check live
docs when the OS or entitlement behavior may have changed.

## Non-negotiable platform boundaries

- Treat Apple Family Sharing authorization and the app's own relationship model as
  separate systems. Apple requires a parent or guardian in the same Family Sharing
  group to authorize protected child mode, but that does not require the app to model
  every household as one fixed parent/child tree.
- Individual authorization is voluntary. It does not carry the child-mode protections
  against deleting the controlling app or signing out of iCloud.
- The public APIs shield apps, categories, and web domains on the current device; they
  do not expose a general remote-device-lock operation. Describe a product as pausing
  or shielding apps unless it uses a separate, documented device-management facility.
- The protected device is the enforcement authority. A remote caregiver action is an
  approval or policy command that the protected device validates and applies locally.
- Cloud notifications are change signals, not guaranteed delivery of individual
  commands. Always fetch authoritative state and design a foreground refresh and safe
  offline path.
- Request the Family Controls distribution entitlement early for the main app and for
  every Screen Time API extension that ships with it.

## References — load on demand

- **[family-controls.md](references/family-controls.md)**
  - Authorization modes, Family Sharing constraints, entitlement requests, privacy,
    and onboarding implications. _Read before designing authorization or distribution._

- **[enforcement.md](references/enforcement.md)**
  - Managed Settings shields, Device Activity schedules and callbacks, named stores,
    shield actions, and reliability boundaries. _Read before implementing restriction
    schedules or unlock behavior._

- **[cloudkit-sync.md](references/cloudkit-sync.md)**
  - CKShare permissions and ownership, shared databases, subscriptions, CKSyncEngine,
    and remote-command implications. _Read before choosing CloudKit or building remote
    approvals._

- **[care-network-architecture.md](references/care-network-architecture.md)**
  - A framework-neutral domain shape for nontraditional households, scoped caregiver
    permissions, occurrence-bound approvals, and local enforcement. _Read when planning
    a parental-control product or reviewing a coupled family model._

## Shelf conventions

- Each reference begins with its Apple source URLs and fetch date.
- Distinguish documented behavior from architectural inference.
- Keep framework types behind adapters; domain policy should remain testable without
  importing FamilyControls, ManagedSettings, DeviceActivity, or CloudKit.
- Do not promise behavior based only on simulator tests. Scheduling, authorization,
  extensions, background delivery, reboot, time-zone changes, and revocation require
  real-device coverage.
