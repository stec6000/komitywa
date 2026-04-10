# Phase 7: Server Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.

**Date:** 2026-04-10
**Phase:** 7 — Server Foundation

---

## Gray Areas Selected

User selected: deploy.sh behavior, Logging level
User deferred: Security settings scope (left to Claude's Discretion)

---

## Area: deploy.sh behavior

**Q:** Should deploy.sh stop immediately if any step fails?
**Options:** Yes, stop on first error (Recommended) / No, continue through failures
**Selected:** Yes, stop on first error
**Notes:** Safer for production — won't restart Passenger on a broken migration state.

**Q:** Should deploy.sh also clean up stale .pyc files before restarting?
**Options:** Yes, delete __pycache__ before restart (Recommended) / No, skip .pyc cleanup
**Selected:** Yes, delete __pycache__ before restart
**Notes:** Prevents Passenger from serving stale bytecode after git pull.

**Q:** Should deploy.sh create the logs/ directory if it doesn't exist?
**Options:** Yes, mkdir -p logs/ at start (Recommended) / No, I'll create it manually
**Selected:** Yes, mkdir -p logs/ at start
**Notes:** Idempotent — works on first deploy and subsequent deploys.

---

## Area: Logging level

**Q:** What threshold should go into logs/django.log?
**Options:** WARNING and above (Recommended) / ERROR and above only
**Selected:** WARNING and above
**Notes:** More visibility during initial launch — catches invalid ALLOWED_HOSTS,
deprecation warnings, permission denials, not just crashes.

**Q:** Should the logger also include the request URL and user info in error entries?
**Options:** Yes, include django.request logger (Recommended) / No, root logger only
**Selected:** Yes, include django.request logger
**Notes:** Makes it easy to trace which URL triggered a 500 error.

---

*Discussion log generated: 2026-04-10*
