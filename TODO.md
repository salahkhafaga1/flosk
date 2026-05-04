# Vercel Fix TODO (Updated: Removed legacy 'builds' to fix warning)

## Completed
- [x] Updated vercel.json: Modern config (routes/headers only, no 'builds' warning)

## Next Steps
1. Install Vercel CLI: `npm i -g vercel`
2. `vercel login`
3. Vercel Dashboard: Project Settings > General > Root Directory: `frontend/static`, Framework Preset: Other
4. `vercel --prod`
5. Test: / (index.html), /claim.html, /static/lang.js
6. Push/commit if Git-integrated.
7. Backend: Separate deploy or add /api/* proxy later.
