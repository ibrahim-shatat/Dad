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

## M3 — Push notifications (mobile)  ✅ shipped
Wire M2 events to real phone push on the installed PWA.
- [x] Web Push (VAPID keys, subscribe/unsubscribe endpoints, store subscriptions)
- [x] Push on every notification event (best-effort, stale-subscription cleanup)
- [x] Service worker push + notificationclick handlers; "Enable phone notifications" toggle
- [ ] Per-user notification preferences (future refinement)

## M4 — Phase 2: Better Approval Flow  ✅ shipped
- [x] Edit an email draft before approving (review modal: to/cc/subject/body)
- [x] Require a rejection reason/comment (stored + shown to requester)
- [x] Approval history + who requested / who reviewed (names + review note)
- [x] Filters by type / status
- [x] Clear post-approval behavior per item type (draft locks once actioned)

## M5 — Phase 3: Executive Briefing  ✅ shipped
- [x] Daily briefing page (urgent emails, meetings, action items, approvals, document risks)
- [x] Claude-written executive summary + top priorities
- [x] Mark briefing items handled (persistent, with progress bar)

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
