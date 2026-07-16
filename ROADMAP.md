# Dad — Build Track

One integrated track covering the mobile app (Android PWA), notifications, and all the feature
phases. Each milestone is shipped live (push to `main` → Render + Netlify auto-deploy) so
progress is visible continuously. Check items off as we go.

**Live:** app https://ai-excutive-agent.netlify.app · api https://dad-api-rw61.onrender.com

## Legend
- [ ] not started · [~] in progress · [x] done

---

## M1 — Installable Android app (PWA)  ← current
Same codebase serves web + Android; installable to the home screen, no app store.
- [x] Web app manifest (name, icons, theme, standalone display)
- [x] App icons (192 / 512 / maskable + apple-touch + favicon)
- [x] Service worker (offline shell + asset caching) via vite-plugin-pwa
- [x] "Install app" prompt / hint (dismissible banner)
- [~] Mobile-responsive polish pass on key screens
- [~] Verify install on Android + deploy

## M2 — Notifications (in-app)  ✅ shipped
The foundation everything else surfaces through.
- [x] `notifications` table + model + migration
- [x] Emit events: document reviewed, meeting processed, approval pending/approved/rejected,
      urgent email arrived
- [x] API: list, unread count, mark read/all-read
- [x] Frontend: notification bell + dropdown/center, unread badge, polling

## M3 — Push notifications (mobile)
Wire M2 events to real phone push on the installed PWA.
- [ ] Web Push (VAPID keys, subscribe endpoint, store subscriptions)
- [ ] Push on high-priority events (pending approval, urgent email)
- [ ] Per-user notification preferences

## M4 — Phase 2: Better Approval Flow
- [ ] Edit an email draft before approving
- [ ] Require a rejection reason/comment
- [ ] Approval history + who requested / who reviewed
- [ ] Filters by type / status / date
- [ ] Clear post-approval behavior per item type

## M5 — Phase 3: Executive Briefing
- [ ] Daily briefing page (urgent emails, meetings, action items, approvals, document risks)
- [ ] Claude-written executive summary
- [ ] Mark briefing items handled

## M6 — Phase 4: Calendar Integration
- [ ] Google + Outlook calendar OAuth
- [ ] Show upcoming meetings
- [ ] Meeting-prep briefs; link notes to events
- [ ] Post-meeting follow-up tasks/emails

## M7 — Phase 5: Workspace Search / Chat
- [ ] Search across documents, meetings, emails, presentations
- [ ] Chat ("What needs my approval today?", "Summarize open tasks")
- [ ] Answers keep source links

## M8 — Phase 6: Admin & Production Readiness
- [ ] User management UI
- [ ] Integration settings page
- [ ] Audit logs
- [ ] Rate limiting + retry policies
- [ ] Observability for failed AI jobs / syncs

## Cross-cutting (ongoing)
- [ ] Backend test coverage for documents / meetings / dashboard endpoints
- [ ] Frontend empty / error / loading states
- [ ] Durable file storage (Supabase Storage) so uploads/exports survive restarts
