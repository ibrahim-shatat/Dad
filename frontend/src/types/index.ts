export type UserRole = 'director' | 'assistant' | 'admin'

export interface User {
  id: string
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  created_at: string
}

export type NotificationType =
  | 'document_reviewed'
  | 'meeting_processed'
  | 'approval_pending'
  | 'approval_approved'
  | 'approval_rejected'
  | 'urgent_email'

export interface Notification {
  id: string
  type: NotificationType
  title: string
  body: string | null
  link: string | null
  is_read: boolean
  created_at: string
}

export type ApprovalItemType = 'email_draft' | 'presentation_export' | 'document_share' | 'dummy'
export type ApprovalStatus = 'pending' | 'approved' | 'rejected'

export interface ApprovalQueueItem {
  id: string
  item_type: ApprovalItemType
  reference_id: string
  preview_text: string
  requested_by_id: string
  requested_by_name: string | null
  status: ApprovalStatus
  reviewed_by_id: string | null
  reviewed_by_name: string | null
  reviewed_at: string | null
  review_note: string | null
  created_at: string
}

export type SearchResultType =
  | 'document'
  | 'meeting'
  | 'email'
  | 'presentation'
  | 'event'
  | 'approval'

export interface SearchResult {
  type: SearchResultType
  id: string
  title: string
  snippet: string | null
  link: string
}

export interface ChatSource {
  label: string
  link: string
}

export interface ChatResponse {
  answer: string
  sources: ChatSource[]
}

export interface CalendarEvent {
  id: string
  account_id: string
  title: string
  description: string | null
  location: string | null
  start_time: string
  end_time: string | null
  is_all_day: boolean
  organizer: string | null
  attendees: string[]
  prep_brief: string | null
  prep_generated_at: string | null
  created_at: string
}

export interface BriefingItem {
  key: string
  title: string
  subtitle: string | null
  detail: string | null
  link: string | null
  severity: 'low' | 'medium' | 'high' | null
  handled: boolean
}

export interface BriefingSection {
  id: string
  label: string
  items: BriefingItem[]
}

export interface Briefing {
  briefing_date: string
  summary: string | null
  top_priorities: string[]
  generated_at: string | null
  sections: BriefingSection[]
  total_items: number
  handled_items: number
}

export type DocumentStatus =
  | 'uploaded'
  | 'extracting'
  | 'extracted'
  | 'reviewing'
  | 'reviewed'
  | 'failed'

export interface RiskFlag {
  category: string
  description: string
  severity: 'low' | 'medium' | 'high'
}

export interface DocumentReview {
  id: string
  executive_summary: string
  risk_flags: RiskFlag[]
  suggested_rewrite: string
  disclaimer_ack: boolean
  model_used: string
  created_at: string
}

// Named DocumentItem, not Document, to avoid colliding with the DOM's global Document type.
export interface DocumentItem {
  id: string
  filename: string
  mime_type: string
  file_size: number
  instructions: string | null
  status: DocumentStatus
  failure_reason: string | null
  created_at: string
  review: DocumentReview | null
}

export type PresentationStatus = 'draft' | 'generating' | 'ready' | 'approved' | 'failed'
export type SlideLayout = 'section_header' | 'bullets' | 'two_column' | 'chart'

export interface SlideChart {
  categories: string[]
  values: number[]
  series_name: string
}

export interface SlideContent {
  layout: SlideLayout
  title: string
  bullets: string[]
  left_column: string[]
  right_column: string[]
  chart: SlideChart | null
  speaker_notes: string
}

export interface PresentationOutline {
  title: string
  slides: SlideContent[]
}

export interface PresentationItem {
  id: string
  source_document_id: string | null
  title: string | null
  instructions: string | null
  structured_content: PresentationOutline | null
  status: PresentationStatus
  failure_reason: string | null
  created_at: string
}

export type MeetingStatus = 'processing' | 'processed' | 'failed'
export type ActionItemStatus = 'open' | 'in_progress' | 'done'
export type DecisionStatus = 'pending' | 'decided' | 'deferred'
export type EmailDraftStatus = 'pending_approval' | 'approved' | 'rejected' | 'sent'

export interface ActionItem {
  id: string
  description: string
  owner: string
  due_date: string | null
  status: ActionItemStatus
  created_at: string
}

export interface Decision {
  id: string
  description: string
  decided_by: string
  status: DecisionStatus
  deadline: string | null
  created_at: string
}

export interface EmailDraft {
  id: string
  source_meeting_id: string | null
  account_id: string | null
  source_message_id: string | null
  to_addresses: string[]
  cc_addresses: string[]
  subject: string
  body: string
  status: EmailDraftStatus
  sent_at: string | null
  created_at: string
}

export type EmailProvider = 'gmail' | 'outlook'
export type EmailUrgency = 'low' | 'medium' | 'high'

export interface EmailAccount {
  id: string
  provider: EmailProvider
  email_address: string
  last_synced_at: string | null
  created_at: string
}

export interface EmailMessageItem {
  id: string
  account_id: string
  provider_message_id: string
  thread_id: string | null
  sender: string
  subject: string
  snippet: string
  received_at: string
  is_unread: boolean
  ai_urgency: EmailUrgency | null
  ai_summary: string | null
}

export interface MeetingItem {
  id: string
  title: string
  meeting_date: string
  instructions: string | null
  summary: string | null
  status: MeetingStatus
  failure_reason: string | null
  action_items: ActionItem[]
  decisions: Decision[]
  email_drafts: EmailDraft[]
  created_at: string
}

export interface UpcomingDeadline {
  type: 'action_item' | 'decision'
  id: string
  description: string
  owner: string
  due_date: string
  meeting_id: string
  meeting_title: string
}

export interface DashboardSummary {
  pending_approvals: ApprovalQueueItem[]
  documents_awaiting_review: number
  presentations_in_progress: number
  open_action_items: number
  upcoming_deadlines: UpcomingDeadline[]
  unread_urgent_emails: number
}
