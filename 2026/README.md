# CrewHub — Real-Time Hackathon Team Formation & Synergy Matchmaking Platform

A full-stack, real-time collaboration and talent matchmaking platform designed for competitive hackathons, project sprints, and collaborative engineering teams. CrewHub replaces unorganized chat channels with structured team boarding manifests, verified GitHub & LinkedIn developer portfolios, real-time Firestore synchronization, and a deterministic skill-synergy matching algorithm.

---

## 1. System Architecture

The application is built on a modern, decoupled client-server architecture:

```
[ Client Application (Vite + React 19 + TypeScript) ]
                     │
                     ├───> Real-Time WebSocket/Streams ───> [ Google Firebase Firestore NoSQL Database ]
                     │                                      (Users, Projects, Join Requests, Chats)
                     │
                     └───> REST API Endpoints (/api/*) ───> [ Node.js & Express API Gateway ]
                                                                 │
                                                                 ├──> PBKDF2 Password Hashing
                                                                 ├──> GitHub REST API v3 Integration
                                                                 ├──> LinkedIn Profile URL Verification
                                                                 └──> Gemini AI Synergy Summarizer
```

- **Frontend Tier**: React 19, TypeScript, Tailwind CSS v4, Motion (fluid micro-interactions), Lucide Icons.
- **Backend / Middleware Tier**: Node.js, Express, PBKDF2 Cryptographic Hashing, GitHub REST API v3 client.
- **Database & Auth Tier**: Google Cloud Firebase Firestore (NoSQL cloud document store with real-time listeners and declarative security rules) and Firebase Authentication.
- **Intelligent Synergy Engine**: Deterministic multi-factor scoring algorithm (weighted skill taxonomy, role alignment, domain overlap, and repository telemetry).

---

## 2. Database Scope & Data Models

CrewHub operates on **Google Cloud Firebase Firestore**, a cloud-hosted NoSQL document database providing millisecond-latency synchronization across clients.

### 2.1 Collection Schemas

#### 1. `users` Collection (Builder Profiles)
Stores user credentials, verified social links, and canonical technical skills.
```json
{
  "uid": "string (Firebase Auth UID)",
  "email": "string",
  "name": "string",
  "headline": "string (e.g. Full-Stack Developer & IoT Enthusiast)",
  "bio": "string",
  "avatarUrl": "string (URL or base64 data URI)",
  "githubUrl": "string (verified link)",
  "githubData": {
    "handle": "string",
    "publicRepos": "number",
    "followers": "number",
    "topLanguages": ["string"],
    "recentCommits": "number"
  },
  "linkedinUrl": "string (verified link)",
  "skills": ["string (canonical taxonomy entries)"],
  "roles": ["string (predefined roles)"],
  "domains": ["string (multi-select domain specializations)"],
  "skillLevel": "beginner | intermediate | advanced",
  "createdAt": "timestamp"
}
```

#### 2. `projects` Collection (Hackathon Project Manifests)
Stores project specifications, vacant positions, tech stacks, and live GitHub tracking.
```json
{
  "id": "string (auto-generated document ID)",
  "title": "string",
  "description": "string",
  "domains": ["IoT", "Web Development", "AI/ML"],
  "requiredSkills": ["React", "TypeScript", "ESP32", "Python"],
  "teamSize": "number",
  "deadline": "string (ISO Date or timestamp)",
  "openRoles": [
    {
      "role": "Embedded/Firmware Developer",
      "description": "Firmware programming with C++ and FreeRTOS",
      "filled": false,
      "filledBy": null
    }
  ],
  "leaderId": "string (UID of creator)",
  "leaderName": "string",
  "leaderAvatar": "string",
  "members": ["array of user UIDs"],
  "githubRepoUrl": "string (e.g. https://github.com/owner/repo)",
  "githubStats": {
    "totalCommits": 18,
    "progressPct": 90,
    "openIssues": 2,
    "stars": 4,
    "lastPushed": "2026-10-29T10:00:00Z"
  },
  "createdAt": "timestamp"
}
```

#### 3. `joinRequests` Collection (Team Applications)
Tracks applications submitted by builders to join specific project rosters.
```json
{
  "id": "string",
  "projectId": "string",
  "projectTitle": "string",
  "applicantId": "string",
  "applicantName": "string",
  "applicantAvatar": "string",
  "targetRole": "string",
  "pitch": "string",
  "status": "pending | accepted | rejected",
  "createdAt": "timestamp"
}
```

#### 4. `messages` Collection (Real-Time Team War-Room Chat)
Provides private channel communication for accepted team members.
```json
{
  "id": "string",
  "projectId": "string",
  "senderId": "string",
  "senderName": "string",
  "senderAvatar": "string",
  "content": "string",
  "codeSnippet": "string (optional)",
  "createdAt": "timestamp"
}
```

---

## 3. Deterministic Matchmaking Algorithm

Rather than relying on non-deterministic or opaque scoring, CrewHub implements a transparent, mathematically rigorous 4-factor scoring model:

$$\text{Score} = (0.50 \times S_{\text{skills}}) + (0.25 \times R_{\text{roles}}) + (0.15 \times D_{\text{domains}}) + (0.10 \times F_{\text{fit}})$$

1. **Skill Overlap ($S_{\text{skills}} = 50\%$)**: 
   - Uses a canonical skills taxonomy (`src/data/taxonomy.ts`) mapping software and hardware aliases (e.g., `"arduino IDE"` $\rightarrow$ `"Arduino"`, `"cpp"` $\rightarrow$ `"C++"`).
   - Jaccard similarity index between the candidate's verified skills and project requirements.
2. **Role Fit ($R_{\text{roles}} = 25\%$)**:
   - Matches candidate's declared roles against project's unfulfilled open positions.
3. **Domain Alignment ($D_{\text{domains}} = 15\%$)**:
   - Evaluates domain intersection (e.g., IoT, Embedded Systems, AI/ML, Fintech).
4. **Experience & GitHub Telemetry ($F_{\text{fit}} = 10\%$)**:
   - Accounts for self-declared proficiency combined with verified GitHub repository activity and commit history.

---

## 4. How to Open and Run in Visual Studio Code

### Step 1: Open the Project in VS Code
1. Open Visual Studio Code.
2. Click **File > Open Folder...** and select the root directory of this project (`crewhub`).
3. Open the built-in terminal in VS Code using the shortcut:
   - **macOS**: `Ctrl + \`` or `Cmd + Shift + P > Terminal: Create New Terminal`
   - **Windows / Linux**: `Ctrl + \``

### Step 2: Install Node Dependencies
Ensure Node.js (version 18 or higher) is installed on your machine. In the VS Code terminal, run:
```bash
npm install
```

### Step 3: Configure Environment Variables
Copy the `.env.example` file to create your `.env`:
```bash
cp .env.example .env
```
*(Firebase configuration is pre-configured in `firebase-applet-config.json` and loads automatically without requiring external setup).*

### Step 4: Run the Development Server
Launch the full-stack development environment:
```bash
npm run dev
```

The application will start on:
```
http://localhost:3000
```
Open this URL in Google Chrome, Microsoft Edge, or any modern web browser.

---

## 5. Live Demonstration & Verification Guide for Faculty

When presenting to faculty members, use this workflow to demonstrate real-time data persistence and full-stack capabilities:

### Test Case 1: Real-Time Multi-Client Synchronization
1. Open two browser windows side-by-side:
   - Window A: Logged in as User 1 (Project Creator).
   - Window B: Incognito window logged in as User 2 (Applicant).
2. In Window A, navigate to **Create Team** and publish a new project ticket.
3. Observe Window B: The new project card appears **instantly in the Browse feed without refreshing the page**, demonstrating Firestore snapshot listeners.

### Test Case 2: Applicant Join Request & Team Roster Live Update
1. From Window B, click on the project, select an open role, and click **Send Join Request**.
2. Observe Window A: The notification badge increments and the applicant appears in the Project Leader's review dashboard.
3. In Window A, click **Accept Request**.
4. Both windows update simultaneously: User 2 is assigned to the role, and the project's War-Room chat unlocks for both members.

### Test Case 3: Live GitHub Telemetry Sync
1. In the project creation form, enter a public GitHub repository URL (e.g., `https://github.com/facebook/react` or your own personal repo).
2. The backend connects directly to the GitHub REST API v3 to pull commit count, open issues, and calculate a milestone progress bar.

### Test Case 4: Inspecting Database in Firebase Console
The database is hosted on Google Cloud Firebase Firestore:
- **Firebase Project ID**: `divine-link-k61jg`
- **Database Instance**: `ai-studio-7159676d-a8c7-49af-ac2e-45a72f2d331b`
- **Web Console Link**: [Google Firebase Console](https://console.firebase.google.com/)
- Under **Build > Firestore Database**, you can observe documents dynamically writing to `users`, `projects`, `joinRequests`, and `messages` in real time.

---

## 6. Project Directory Structure

```
├── package.json               # Dependencies and build scripts
├── vite.config.ts             # Vite configuration with Express API middleware
├── tsconfig.json              # TypeScript compilation rules
├── firebase-applet-config.json# Firebase configuration keys & database identifier
├── firestore.rules            # Declarative NoSQL database security rules
├── server.ts                  # Production Node.js server entry point
├── server/
│   └── api.ts                 # Express REST API (password hashing, GitHub & URL verification)
├── src/
│   ├── main.tsx               # React application entry point
│   ├── App.tsx                # Main view router & state controller
│   ├── firebase.ts            # Firebase SDK initialization & Firestore references
│   ├── index.css              # Tailwind CSS stylesheet
│   ├── data/
│   │   └── taxonomy.ts        # Canonical skills taxonomy, hardware/software aliases, matching formula
│   └── components/
│       ├── LandingPage.tsx        # Hero banner & interactive manifest demo
│       ├── AuthModal.tsx          # Authentication (Google OAuth & salted email/password)
│       ├── ProfileSetupModal.tsx  # Developer profile builder with URL verification
│       ├── BrowseProjects.tsx     # Project ticket feed with AI synergy cards
│       ├── CreateProjectModal.tsx # Team manifest builder with instant skill suggestions
│       ├── ProjectDetailModal.tsx # Boarding pass view & join application
│       ├── DashboardView.tsx      # Leader applicant management & member rosters
│       └── ChatModal.tsx          # Real-time team collaboration war-room
```

---

## 7. Security & Best Practices

- **Password Storage**: Passwords are never saved in plaintext; hashed via PBKDF2 with unique salts before authentication.
- **Access Control**: Governed by `firestore.rules`, ensuring only authorized project members can access private team war-room chats.
- **Sanitization**: All user-submitted text and GitHub parameters are sanitized and validated to mitigate XSS and injection vulnerabilities.
