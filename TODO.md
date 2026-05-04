# Vercel Fix TODO

## Completed
- [x] Created vercel.json for static frontend deployment (maps / to frontend/static/, fixes routes/caching)

## Next Steps
1. Install Vercel CLI if needed: `npm i -g vercel`
2. Login: `vercel login`
3. Deploy: `vercel --prod`
4. Test deployed URL (routes: /index.html, /static/lang.js etc.)
5. Push to GitHub if using Git integration.
6. Monitor Vercel logs for any remaining 404s.
7. Optional: Add backend API proxy if needed (e.g., route /api/* to Python functions).
