Background

https://docs.lovable.dev/features/security Read through this doucmentation.

Here are security patterns that you must follow to ensure your website is good and has no very bad security flaws (though it won't be 100% because there will be always flaws in any website by anyone!):
Trusting Client Data: Using form/URL input directly.
Fix: Always validate & sanitize on server; escape output.
Secrets in Frontend: API keys/creds in React/Next.js client code.
Fix: Keep secrets server-side only (env vars, ensure .env is in .gitignore).
Weak Authorization: Only checking if logged in, not if allowed to do/see something.
Fix: Server must verify permissions for every action & resource.
Leaky Errors: Showing detailed stack traces/DB errors to users.
Fix: Generic error messages for users; detailed logs for devs.
No Ownership Checks (IDOR): Letting user X access/edit user Y's data via predictable IDs.
Fix: Server must confirm current user owns/can access the specific resource ID.
Ignoring DB-Level Security: Bypassing database features like RLS for fine-grained access.
Fix: Define data access rules directly in your database (e.g., RLS).
Unprotected APIs & Sensitive Data: Missing rate limits; sensitive data unencrypted.
Fix: Rate limit APIs (middleware); encrypt sensitive data at rest; always use HTTPS.

Implementation Plan

“Audit my project for security issues: public Supabase endpoints, unsecured API routes, weak or missing access control, and improperly configured auth rules. Specifically: 1. Check if Supabase tables or RPC functions are publicly accessible without proper Row Level Security (RLS) or role-based permissions. 2. Confirm that users can’t upgrade their own account privileges or delete/edit other users’ data. 3. Ensure all write operations (POST, PUT, PATCH, DELETE) are protected by server-side auth and validation, not just client checks. 4. Identify any hardcoded secrets, misconfigured environment variables, or sensitive data leaks. 5. Generate a security checklist based on my current stack and suggest immediate high-priority fixes.
Assume I want to go from a vibe-coded prototype to a real production-ready app. Refactor anything risky, and explain what you’re doing as you go.”
