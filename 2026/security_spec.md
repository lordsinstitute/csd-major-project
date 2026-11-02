# Security Specification for CrewHub

## 1. Data Invariants
1. A user can only create and modify their own `/users/{userId}` profile document where `userId == request.auth.uid`.
2. Any project document must have an authentic `leaderId` matching `request.auth.uid`.
3. Only the leader of a project or current accepted project members can read messages in `/projects/{projectId}/messages/{messageId}`.
4. Only an accepted project member can write messages to `/projects/{projectId}/messages/{messageId}`.
5. Applicants can create join requests with `applicantId == request.auth.uid`.
6. Only the project `leaderId` or `applicantId` can read a join request.
7. Only the project `leaderId` can update the status of a join request to 'accepted' or 'declined'.
8. A user cannot impersonate another student's UID on any creation or update.
9. All string fields must adhere to strict size bounds to prevent Denial of Wallet.
10. Catch-all default deny is enforced on all other documents.

## 2. The Dirty Dozen Payloads (Negative Tests)
1. **P1 (Identity Spoofing - Profile)**: Creating a user doc at `/users/victimUid` with attacker auth UID -> Denied.
2. **P2 (Orphan Message)**: Posting a chat message to a project where the sender is not in `memberIds` or `leaderId` -> Denied.
3. **P3 (Malicious Role Escalation)**: Regular member updating a project doc's `leaderId` to themselves -> Denied.
4. **P4 (Request Spoofing)**: Submitting a `joinRequest` where `applicantId != request.auth.uid` -> Denied.
5. **P5 (Unauthorized Status Change)**: Applicant approving their own join request (`status: 'accepted'`) -> Denied.
6. **P6 (Outsider Snooping - Chat)**: Non-member querying `/projects/{projectId}/messages` -> Denied.
7. **P7 (Outsider Snooping - Join Requests)**: Random student querying join requests belonging to other leaders and applicants -> Denied.
8. **P8 (Denial of Wallet String Injection)**: Injecting 2MB payload into message text -> Denied (`maxLength` 4000 violated).
9. **P9 (Immortal Field Mutation)**: Mutating `applicantId` or `projectId` on an existing join request -> Denied.
10. **P10 (Shadow Keys)**: Submitting unknown keys (`isAdmin: true`, `godMode: true`) in user profile -> Denied.
11. **P11 (Unauthenticated Read/Write)**: Accessing project chat without authentication -> Denied.
12. **P12 (Audit Log Tampering)**: Deleting or modifying a reported violation in `/reports` -> Denied.
