# Dad — AI Executive Assistant · UI/UX Design Brief for Stitch

This is a single, complete design brief for a multi-screen app. Read all of it, then design **every
screen listed in section 3**, plus the shared components, in **both mobile and desktop** and **both
light and dark mode**, all using one consistent visual language (section 1). Keep the indigo primary,
the calm card-based style, and the AI-sparkle accent identical across every screen.

---

## 0. Product context (read first)

**What it is:** "Dad" is an AI executive assistant dashboard for a company **director** and their
**assistant**. AI reads their email, meetings, and documents; it summarizes, drafts, and flags
risks. Crucially, **nothing sensitive is sent or finalized until a human approves it** — there is
an approval queue at the heart of the product.

**Who uses it:** busy, non-technical executives. Primary device is an **Android phone** (installed
as a PWA / home-screen app), but it's also used on desktop. **Design mobile-first, then desktop.**

**Emotional tone:** calm, trustworthy, "quiet confidence." It should feel like a competent chief
of staff — never noisy, playful, or cluttered. Reduce anxiety: make it obvious what needs
attention and what's already handled.

**Roles:** `director`, `assistant`, `admin`. Admin-only screens are marked.

---

## 1. Design system (paste this into Stitch first)

**Style:** modern professional SaaS. Clean, spacious, card-based. Soft, not flashy. Think Linear /
Notion / Stripe dashboard calm — but warmer.

**Color**
- Primary / brand: deep indigo-blue `#4F46E5` (actions, active nav, links, AI accents).
- Primary hover: slightly darker / 90% opacity.
- Background: near-white `#FAFAFA` (light) / near-black `#0B0B0F` (dark).
- Surface / cards: `#FFFFFF` (light) / `#17171C` (dark), with a hairline border `#E5E7EB` /
  `#26262E`.
- Text: `#111827` primary, `#6B7280` muted (light); invert for dark.
- Semantic: **red** `#EF4444` destructive / urgent / high severity; **amber** `#F59E0B` warning /
  medium severity / pending; **green** `#16A34A` success / approved / "all clear"; **blue** info.
- AI moments use a subtle primary tint background (`primary @ 8–10% opacity`) with a sparkle icon.

**Support full light AND dark mode.**

**Typography:** Inter (or system sans). Page title 24–28px semibold; section heading 16–18px
semibold; body 14px; meta/caption 11–12px muted. Generous line-height for readability.

**Shape & elevation:** rounded corners — cards `rounded-xl` (12–16px), buttons/inputs `rounded-md`
(8px), chips/badges pill (full). Shadows are soft and low (`shadow-sm`); rely on borders more than
heavy shadows. Comfortable padding (16–24px in cards).

**Iconography:** Lucide-style line icons, 16–20px, `1.5` stroke. Consistent, minimal.

**Motion:** subtle. 150–200ms ease transitions, gentle slide/fade for drawers, dropdowns, and
modals. No bouncy or attention-grabbing animation.

**Accessibility:** WCAG AA contrast, visible focus rings (2px primary), 44px min tap targets on
mobile, never color-only signals (pair color with icon/label).

**Reusable components** (design these consistently everywhere):
- **Button**: variants `primary` (filled indigo), `outline`, `ghost`, `destructive` (red). Sizes
  sm/default. Icon+label allowed.
- **Card**: header (title + optional action/badge), content, optional footer with actions.
- **Badge / chip**: pill. Variants: default (indigo), muted (gray), success (green), warning
  (amber), destructive (red), outline. Used for status + severity.
- **Input / textarea / select / label**: bordered, `rounded-md`, clear focus ring.
- **Modal / bottom sheet**: centered dialog on desktop; slides up from bottom on mobile.
- **Empty state**: centered icon + one calm sentence + (optional) a single primary action.
- **Loading**: skeleton rows/cards, or a quiet "Loading…" line. Never spinners that dominate.
- **Toast**: bottom, brief, low-key.
- **Severity dot**: small colored dot (red/amber/gray) next to a label.

---

## 2. Global layout & navigation

**⎘ Stitch prompt — App shell / navigation**
> Design the app shell for a professional AI executive-assistant dashboard, light and dark mode.
> **Desktop:** a fixed left sidebar (240px) on a white/near-black surface with a hairline right
> border. Sidebar top: small app title "AI Executive Assistant". Nav list of items, each an icon +
> label, with the active item filled in indigo with white text and rounded corners; inactive items
> are gray with a subtle hover. Nav items in order: Dashboard, Daily briefing, Assistant, Documents,
> Presentations, Email, Meetings, Calendar, Approvals, and (admin only) Admin. Sidebar bottom shows
> the current user's name + role and a "Log out" ghost button. Main area to the right: a slim top
> bar aligned right containing a notification bell icon with a small red unread count badge; below
> it, the page content on a `#FAFAFA` background with 24px padding.
> **Mobile:** replace the sidebar with a sticky top bar (hamburger menu icon on the left, app title,
> notification bell on the right). Tapping the hamburger slides in the sidebar as a left drawer over
> a dim backdrop. Everything is single-column and thumb-reachable.

**Notification bell + dropdown**
**⎘ Stitch prompt — Notifications dropdown**
> Design a notification bell button with a small red count badge, and its dropdown panel (width
> ~320px, on mobile max full-width minus margins). Panel header: "Notifications" with a "Mark all
> read" text link on the right. A scrollable list of notification rows: each row has a small
> unread-dot on the left when unread (unread rows have a faint indigo tint), a bold one-line title,
> a two-line muted body, and a relative timestamp ("2m ago"). Types include: document reviewed,
> meeting processed, approval pending/approved/rejected, urgent email. Empty state: "No notifications
> yet." Panel footer: a full-width ghost button with a small bell icon, label "Enable phone
> notifications" (toggles to "Phone push on — tap to turn off").

---

## 3. Screens

### 3.1 Login
**⎘ Stitch prompt — Login**
> Design a clean, centered login screen for a professional AI executive assistant, light and dark
> mode. A single card (max ~400px) centered on a calm background. Card contains: the app name "AI
> Executive Assistant" with a small logo mark, a short muted tagline, an email field, a password
> field, and a full-width indigo "Sign in" button. Show an inline error banner state for "Incorrect
> email or password." Minimal, confident, no marketing clutter. Also show a subtle "too many
> attempts, try again shortly" rate-limit message variant.

### 3.2 Dashboard (home)
Purpose: at-a-glance status the moment they open the app.
**⎘ Stitch prompt — Dashboard**
> Design a dashboard home screen for an AI executive assistant, mobile-first then desktop, light and
> dark mode. Top: a greeting/title. A responsive grid of small **stat cards**: "Documents awaiting
> review", "Presentations in progress", "Open action items", "Unread urgent emails" — each a card
> with a label, a large number, and a small icon; urgent/nonzero counts use an amber or red accent.
> Below, a section "Upcoming deadlines" listing action items and decisions with owner, due date
> (overdue in red), and source meeting. Then a section "Pending approvals" showing the first few
> approval cards (title, type, timestamp, Approve/Reject buttons) with a "View all" link to the
> Approvals page. Everything card-based, calm, scannable. Include a loading skeleton state and an
> empty "You're all caught up" state.

### 3.3 Daily briefing
Purpose: a "start of day" page; AI summary + a checklist of what needs attention.
**⎘ Stitch prompt — Daily briefing**
> Design a "Daily briefing" screen for an executive, light and dark mode. Header: a sun icon in an
> indigo-tinted rounded square, title "Daily briefing", today's date, and a primary "Generate
> briefing" / "Regenerate" button on the right. First card = **Executive summary**: a sparkle icon +
> "Executive summary" heading, a few sentences of AI-written narrative, then a "Top priorities"
> numbered list (up to 3), and a small "Generated 9:14 AM" timestamp. Below the summary, a thin
> **progress bar** with "3/7 handled". Then grouped sections — "Urgent emails", "Meetings today",
> "Action items due", "Waiting on your approval", "Document risks" — each a small heading with a
> count, followed by item rows. **Each item row** has a round check button on the left (empty circle
> → filled indigo check when handled; handled rows dim and strike-through the title), a colored
> severity dot, a bold title, a muted subtitle (e.g. "Alex · due Jul 18 (overdue)"), and an optional
> two-line detail; tapping the row navigates to the source. Include an "all clear / nothing pressing"
> celebratory empty state and a "no summary yet — tap Generate" state.

### 3.4 Assistant (search + chat)
Purpose: ask questions about the workspace and search across everything.
**⎘ Stitch prompt — Assistant (chat + search)**
> Design an "Assistant" screen combining an AI chat and a global search, light and dark mode. Title
> "Assistant" + subtitle "Ask about your workspace, or search across everything." **Chat card**: a
> scrollable message thread — the user's messages are indigo bubbles aligned right, the assistant's
> are gray bubbles aligned left. Assistant messages can include a row of small **source chips**
> below the text (clickable pills that link to the cited item). When empty, show a sparkle prompt
> "Ask me anything about your work. Try:" with tappable suggestion chips ("What needs my approval
> today?", "Summarize my open action items", "What's on my calendar this week?", "Any urgent emails
> I should know about?"). A "Thinking…" bubble appears while waiting. Bottom: a text input + send
> button (paper-plane icon). **Below the chat, a Search section:** a search input with a magnifier
> icon; as you type (2+ chars) it shows a list of typed results — each result row has a small type
> icon in a muted square, an UPPERCASE type label (Document / Meeting / Email / Presentation / Event
> / Approval), a bold title, and a muted snippet; tapping navigates to it. Show "No matches" and
> initial idle states.

### 3.5 Approvals queue
Purpose: the safety core — approve/reject AI actions; edit email drafts before sending.
**⎘ Stitch prompt — Approvals queue**
> Design an "Approval queue" screen for an AI assistant where nothing is sent until approved, light
> and dark mode. Title "Approval queue" + reassuring subtitle "Nothing here is sent or finalized
> until you approve it." A filter row: segmented status tabs (Pending / Approved / Rejected / All)
> plus a type dropdown (All types / Email drafts / Presentation exports / Document shares). Below, a
> list of **approval cards**. Each card header: a type title (e.g. "Email draft") and a status badge
> (Pending=gray, Approved=green, Rejected=red); a muted line "Requested by [name] · [date/time]".
> Card body: the preview text. For **pending** items, a footer with buttons: primary "Approve",
> outline "Reject", and for email drafts a ghost "Edit draft" (pencil icon). Tapping "Reject" reveals
> an inline textarea "Why are you rejecting this? (required)" with "Confirm reject" (red) and
> "Cancel". For **already-reviewed** items, show a muted panel: "Approved/Rejected by [name] · [date]"
> and, if present, the reviewer's note/reason. Include an empty "Nothing pending approval" state.

**⎘ Stitch prompt — Email draft editor (modal / bottom sheet)**
> Design a modal (centered on desktop, bottom sheet sliding up on mobile) titled "Review email
> draft" with a close X. Body form fields: To (comma-separated emails), Cc, Subject, and a large
> Body textarea — all pre-filled and editable. If the draft is no longer editable, show a muted
> banner "This draft is approved and can no longer be edited" and disable the fields. Footer: outline
> "Close" and primary "Save changes" (shows "Saving…"). This is where a human edits an AI-drafted
> email before it goes to the approval decision.

### 3.6 Documents
Purpose: upload documents; AI extracts text, writes an executive summary, and flags risks.
**⎘ Stitch prompt — Documents list**
> Design a "Documents" screen, light and dark mode. Header with title and an "Upload document"
> primary button (with an upload icon) that opens a small upload form (file picker + optional
> instructions textarea). Below, a list/grid of document cards: filename with a file-type icon, a
> **status badge** (Uploaded, Extracting, Extracted, Reviewing, Reviewed=green, Failed=red), created
> date, and a one-line summary preview when reviewed. In-progress items show a subtle animated
> status. Tapping a card opens its detail. Include empty and loading states.

**⎘ Stitch prompt — Document detail (AI review)**
> Design a document detail screen showing an AI review, light and dark mode. Top: filename, status
> badge, and metadata (type, size, uploaded date). Section "Executive summary": a card with the
> AI-written summary and a small sparkle/AI label. Section "Risk flags": a list of flagged issues —
> each is a card/row with a **severity badge** (High=red, Medium=amber, Low=gray), a short category
> label, and a plain-English description. Section "Suggested rewrite": improved wording in a distinct
> block (e.g. a subtle bordered/quote style) with a "Copy" button. Show a "Failed" state with the
> failure reason and a retry action. Keep it readable and reassuring, not alarming.

### 3.7 Presentations
Purpose: generate a slide deck (.pptx) from a document or notes; export goes through approval.
**⎘ Stitch prompt — Presentations list**
> Design a "Presentations" screen, light and dark mode. Header + "New presentation" primary button
> (opens a form: source = a document or pasted text, plus optional instructions). List of
> presentation cards: title, status badge (Draft, Generating, Ready=green, Approved, Failed=red),
> created date. Tap opens detail. Empty + loading states.

**⎘ Stitch prompt — Presentation detail**
> Design a presentation detail screen, light and dark mode. Show the title and status. Render the
> AI-generated **outline as a vertical list of slide previews** — each slide card shows its layout
> type (section header / bullets / two-column / chart), the slide title, and its bullets/columns;
> chart slides show a simple bar-chart placeholder; each slide can show speaker notes in a muted
> collapsible area. A "Download .pptx" button (enabled when Ready). Since export is sensitive, a
> "Send to approval" action routes it to the approval queue. Failed state with reason.

### 3.8 Email
Purpose: connect Gmail/Outlook; AI summarizes + flags urgency; draft replies (approval-gated).
**⎘ Stitch prompt — Email**
> Design an "Email" screen for an AI assistant, light and dark mode. Top: a **connected accounts**
> area — if none connected, a friendly card "Connect a Google or Outlook account" with two provider
> buttons (Google, Outlook); if connected, show each account (address, provider, last-synced time)
> with a "Sync" button. Below: a list of email messages, each row showing sender, subject, a muted
> AI one-line summary, received time, an **unread indicator**, and an **urgency badge** (High=red,
> Medium=amber, Low=gray). A high-urgency row is subtly emphasized. Tapping a message opens it and
> offers a "Draft reply" action (with an optional instructions field) — the AI-drafted reply is then
> sent to the approval queue, not sent directly. Include empty ("no messages yet, tap Sync") and
> loading states, and make it clear replies require approval.

### 3.9 Meetings
Purpose: paste meeting notes/transcript; AI writes summary, extracts action items + decisions,
and drafts a follow-up email (approval-gated).
**⎘ Stitch prompt — Meetings list**
> Design a "Meetings" screen, light and dark mode. Header + "Add meeting" primary button (form:
> title, date, pasted notes/transcript, optional instructions). List of meeting cards: title,
> meeting date, status badge (Processing, Processed=green, Failed=red), and a one-line summary
> preview. Tap opens detail. Empty + loading states.

**⎘ Stitch prompt — Meeting detail**
> Design a meeting detail screen, light and dark mode. Top: title, date, status. Section "Summary":
> AI-written summary card. Section "Action items": a list — each with a description, an owner, a due
> date (overdue in red), and a status chip (Open / In progress / Done). Section "Decisions": each
> with description, who decided, a status chip (Decided / Pending / Deferred), and optional deadline.
> Section "Follow-up email": if the AI drafted one, show a preview with a note that it's waiting in
> the approval queue (link to Approvals). Failed state with reason.

### 3.10 Calendar
Purpose: show synced upcoming meetings; generate AI prep briefs; draft post-meeting follow-ups.
**⎘ Stitch prompt — Calendar**
> Design a "Calendar" screen for an AI assistant, light and dark mode. Header: a calendar-clock icon
> in an indigo-tinted square, title "Calendar", subtitle "Upcoming meetings with AI prep briefs and
> follow-ups", and a "Sync" outline button (spins while syncing). If no account is connected, show a
> card "No connected calendar yet. Connect a Google or Outlook account…" with a "Connect an account"
> button. Otherwise, events **grouped by day** (day heading, then event cards). Each **event card**:
> title, time range (or "All day") on the right, and a meta row with location (map-pin icon) and
> attendee count (people icon). For upcoming events, a "Generate prep brief" outline button (with a
> sparkle icon; shows "Writing…" then the brief appears). The **prep brief** renders inside the card
> as a bordered, tinted block with a "Prep brief" sparkle heading and readable multi-line content
> (context, talking points, questions, prep). For past events, a "Draft follow-up email" button that
> confirms "Follow-up sent to approvals". Empty ("no events synced, tap Sync") and loading states.

### 3.11 Admin (admin only)
Purpose: manage users, monitor system health, review the audit trail.
**⎘ Stitch prompt — Admin**
> Design an admin screen with three tabs, light and dark mode. Header: a shield icon in an
> indigo-tinted square, title "Admin", subtitle "Manage users, review the audit trail, and monitor
> system health." A segmented tab control: **Health / Users / Audit log.**
> **Health tab:** a row of stat cards (Users active/total, Failed docs, Failed meetings, Failed
> slides — nonzero failures in red); a "Connected accounts" card listing each account with provider
> and last-synced time; a "Recent job failures" card (amber warning icon) listing failed background
> jobs with type, error detail, and time — or a cheerful "No background job failures logged." empty
> state.
> **Users tab:** a list of user rows (name + "(you)" tag, email, a role dropdown, and an
> Activate/Deactivate button; your own row's controls are disabled to prevent self-lockout). Below,
> an "Add a user" card with a form (full name, email, temporary password, role dropdown) and a
> "Create user" button; show an inline error state.
> **Audit log tab:** a dense, readable list of audit entries — each row has a small monospace action
> tag (e.g. `auth.login`, `approval.approve`, `user.update`, `job.failed`), the actor's email (or
> "system"), a right-aligned timestamp, and an optional muted detail line.

---

## 4. Cross-cutting states to design (apply to every screen)
- **Loading:** skeletons or a quiet line — never block the whole screen.
- **Empty:** centered icon + one calm sentence + at most one action.
- **Error:** a short, non-technical message with a retry where relevant.
- **AI in progress:** subtle ("Writing…", "Thinking…") with a sparkle, never a big spinner.
- **Offline / PWA:** the app is installable to the Android home screen; include a small dismissible
  "Install app" banner concept (icon + "Add Dad to your home screen" + Install / Dismiss).
- **Approval-first reassurance:** anywhere an email/export is generated, visibly reinforce that it
  waits for human approval before anything leaves.

## 5. Deliverables I'd love back from Stitch
For each screen above: mobile + desktop, light + dark. Plus the shared component sheet (buttons,
badges, cards, inputs, modal, chips, severity dots) so everything stays consistent. Keeping the
indigo primary, the calm card-based language, and the AI-sparkle accent consistent across all
screens is the most important thing.
