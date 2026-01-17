# Team Engineering Playbook

This document explains **how our team builds, ships, and operates software**.
If you’re new, read this first before pushing code to `main`.

---

## 🚦 How Work Flows on This Team

### 1. Picking Up Work

* All work lives in **GitHub Issues**
* Issues are tagged by:

  * `good-first-issue`
  * `backend`, `frontend`, `infra`
  * `blocked`, `needs-design`
* If unclear, ask in **#eng-help** before starting

---

### 2. Branching Strategy

* `main` is **always deployable**
* Create feature branches from `main`:

  ```
  feature/<short-description>
  fix/<bug-name>
  chore/<cleanup-task>
  ```
* No direct pushes to `main`

---

### 3. Pull Request Expectations

Every PR should include:

* What changed (1–3 bullets)
* Why it was needed
* How to test it
* Screenshots (for frontend)

**Good PR title**

```
feat(auth): add refresh token rotation
```

**Bad PR title**

```
fix stuff
```

---

## 🧪 Testing & Quality Bar

### Required Before Merge

* ✅ Tests passing in CI
* ✅ Lint checks clean
* ✅ At least **1 approval**
* ✅ No unresolved comments

### Test Coverage Guidelines

* Backend: business logic + edge cases
* Frontend: core user flows
* Infra: sanity checks, not perfection

---

## 🚀 Deployments

* Deploys happen automatically from `main`
* Production deploys are:

  * Weekdays only
  * Avoid Fridays after 3 PM
* If your change impacts users, post in **#deploys**

---

## 🧠 Decision Making

### Small Decisions

* Make the call
* Document it in the PR

### Big Decisions

* Start a short design doc
* Get async feedback in Slack
* Final decision after 24–48 hours

We value **momentum over perfection**.

---

## 🐛 Handling Incidents & Bugs

### Bug Severity

* **P0:** User-facing outage
* **P1:** Major feature broken
* **P2:** Minor bug or edge case
* **P3:** Nice-to-have fix

### What To Do

1. Acknowledge in Slack
2. Create an issue
3. Fix > explain > document

No blame. We fix systems, not people.

---

## 📚 Where Things Live

* **Docs:** `/docs`
* **Architecture diagrams:** `/docs/architecture`
* **Runbooks:** `/docs/runbooks`
* **Scripts:** `/scripts`
* **Configs:** `/config`

If you can’t find it in 2 minutes, the docs need work.

---

## 💬 Communication Norms

* Slack is async by default
* Use threads
* Status updates go in **#eng-updates**
* Long discussions → GitHub or doc

Silence ≠ blocked. Ask early.

---

## 🎯 What “Good” Looks Like Here

* Small PRs
* Clear intent
* Asking questions early
* Leaving things better than you found them

We care more about **learning speed** than being perfect.

---

*Last Updated: 2026-01-17*
*If something feels outdated or confusing, open a PR to fix it.*
