# Stitch exports

Drop the Stitch-generated screens here (PNG images and/or exported HTML/CSS). Then tell Claude
"the Stitch screens are in design/stitch" and it will read them and implement each screen in the
React app to match. See `../STITCH_BRIEF.md` for the prompt each screen was generated from.

**Naming:** use the numbers below so screens are easy to reference ("do screen 04"). Light/dark or
mobile/desktop variants can add a suffix, e.g. `04-dashboard-dark.png`, `04-dashboard-mobile.png`.

| # | File (suggested) | Screen | Real route |
|---|------------------|--------|------------|
| 01 | `01-app-shell.png` | App shell / navigation (sidebar + mobile drawer) | layout |
| 02 | `02-notifications.png` | Notification bell + dropdown | component |
| 03 | `03-login.png` | Login | `/login` |
| 04 | `04-dashboard.png` | Dashboard (home) | `/dashboard` |
| 05 | `05-briefing.png` | Daily briefing | `/briefing` |
| 06 | `06-assistant.png` | Assistant (chat + search) | `/assistant` |
| 07 | `07-approvals.png` | Approval queue | `/approvals` |
| 08 | `08-draft-editor.png` | Email draft editor (modal / bottom sheet) | component |
| 09 | `09-documents-list.png` | Documents list | `/documents` |
| 10 | `10-document-detail.png` | Document detail (AI review) | `/documents/:id` |
| 11 | `11-presentations-list.png` | Presentations list | `/presentations` |
| 12 | `12-presentation-detail.png` | Presentation detail | `/presentations/:id` |
| 13 | `13-email.png` | Email | `/email` |
| 14 | `14-meetings-list.png` | Meetings list | `/meetings` |
| 15 | `15-meeting-detail.png` | Meeting detail | `/meetings/:id` |
| 16 | `16-calendar.png` | Calendar | `/calendar` |
| 17 | `17-admin.png` | Admin (Health / Users / Audit) | `/admin` |

If you also have the exported code, put it next to the image with the same number, e.g.
`04-dashboard.html`.
