import 'attention_item.dart';

class DashboardSummary {
  final int documentsAwaitingReview;
  final int presentationsInProgress;
  final int openActionItems;
  final int unreadUrgentEmails;
  final int pendingApprovals;
  final List<AttentionItem> needsAttention;

  DashboardSummary({
    required this.documentsAwaitingReview,
    required this.presentationsInProgress,
    required this.openActionItems,
    required this.unreadUrgentEmails,
    required this.pendingApprovals,
    required this.needsAttention,
  });

  factory DashboardSummary.fromJson(Map<String, dynamic> json) {
    final attention = (json['needs_attention'] as List<dynamic>? ?? const [])
        .map((e) => AttentionItem.fromJson(e as Map<String, dynamic>))
        .toList();
    final pending = (json['pending_approvals'] as List<dynamic>? ?? const []).length;
    return DashboardSummary(
      documentsAwaitingReview: (json['documents_awaiting_review'] ?? 0) as int,
      presentationsInProgress: (json['presentations_in_progress'] ?? 0) as int,
      openActionItems: (json['open_action_items'] ?? 0) as int,
      unreadUrgentEmails: (json['unread_urgent_emails'] ?? 0) as int,
      pendingApprovals: pending,
      needsAttention: attention,
    );
  }
}
