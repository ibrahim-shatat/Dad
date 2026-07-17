class EmailMessage {
  final String id;
  final String accountId;
  final String sender;
  final String subject;
  final String snippet;
  final String? aiSummary;
  final String? aiUrgency; // low | medium | high
  final bool isUnread;
  final DateTime receivedAt;

  EmailMessage({
    required this.id,
    required this.accountId,
    required this.sender,
    required this.subject,
    required this.snippet,
    this.aiSummary,
    this.aiUrgency,
    required this.isUnread,
    required this.receivedAt,
  });

  factory EmailMessage.fromJson(Map<String, dynamic> json) => EmailMessage(
        id: json['id'].toString(),
        accountId: json['account_id'].toString(),
        sender: (json['sender'] ?? '') as String,
        subject: (json['subject'] ?? '') as String,
        snippet: (json['snippet'] ?? '') as String,
        aiSummary: json['ai_summary'] as String?,
        aiUrgency: json['ai_urgency'] as String?,
        isUnread: (json['is_unread'] ?? false) as bool,
        receivedAt:
            DateTime.tryParse((json['received_at'] ?? '') as String) ?? DateTime.now(),
      );
}
