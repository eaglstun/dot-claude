# Care-network architecture for parental controls

Sources for the platform constraints (fetched 2026-09-08):

- https://developer.apple.com/documentation/familycontrols
- https://developer.apple.com/documentation/managedsettings/managedsettingsstore
- https://developer.apple.com/documentation/deviceactivity/deviceactivitymonitor
- https://developer.apple.com/documentation/CloudKit/CKShare

The domain guidance below is architectural inference, not an Apple-prescribed schema.

## Avoid permanent global roles

Do not encode a person as globally and exclusively `parent` or `child`. Onboarding may
use those familiar choices to select the first flow, while the durable model represents
relationships and scoped capabilities.

A flexible model contains:

- `Person`: a participant without a permanent family role;
- `CareNetwork`: a household or trusted group, distinct from Apple Family Sharing;
- `Membership`: participation in that network;
- `CareGrant`: capabilities one person has for a particular other person;
- `Device`: the protected physical device assigned to a person;
- `Routine`: schedule, local activity selection, instructions, and release policy;
- `RoutineOccurrence`: one concrete night/morning cycle;
- `AccessRequest`: a request or checklist status from the protected device;
- `Approval`: a one-use authorization for an occurrence;
- `AuditEvent`: append-oriented history of policy and release decisions.

Example CareGrant capabilities include approving release, editing routines, changing
protected activities, viewing status, managing membership, and resetting a fallback
code. Scope them to the person or device they affect.

This shape supports split homes, step-parents, grandparents, limited older-sibling
authority, one caregiver supervising several people, and a person who is supervised in
one relationship while helping someone else.

## Local state machine

Model each routine occurrence explicitly rather than deriving all state from the wall
clock. A compact state machine can distinguish scheduled, restricted, release
requested, released, expired, and failed/recovery states. Record the occurrence ID in
every request and approval so delayed sync cannot release the next morning.

The protected device owns the transition that clears a shield. Remote devices propose
signed or server-authorized commands; they do not directly mutate local framework
state. Domain logic determines whether a command is authorized before calling the
Managed Settings adapter.

Pin the authority root or enrolled caregiver keys during authenticated pairing; a
signature without a trusted bootstrap does not establish who is allowed to act. Track
an authority revision so accepted revocations invalidate older grants locally. An
offline protected device cannot enforce a revocation it has not observed, so surface
pending device acknowledgement rather than promising instantaneous global revocation.

Treat a reusable offline code as a recovery credential. It cannot identify which
currently authorized person entered it, and remote revocation cannot erase knowledge of
a code from an offline device. Define code rotation, administrator-loss recovery, and
device replacement as explicit product lifecycles.

## Boundaries that keep a prototype replaceable

Keep these concerns separate:

- domain models and policy state machine;
- local persistence and App Group extension state;
- Family Controls authorization;
- Device Activity scheduling;
- Managed Settings enforcement;
- cloud synchronization and identity;
- SwiftUI features and navigation.

This permits reuse of proven prototype adapters without inheriting a coupled household
schema, global singleton state, or CloudKit records as view models.
