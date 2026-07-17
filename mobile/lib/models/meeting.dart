class ActionItem {
  final String id;
  final String description;
  final String owner;
  final DateTime? dueDate;
  final String status;

  ActionItem({
    required this.id,
    required this.description,
    required this.owner,
    this.dueDate,
    required this.status,
  });

  factory ActionItem.fromJson(Map<String, dynamic> json) => ActionItem(
        id: json['id'].toString(),
        description: (json['description'] ?? '') as String,
        owner: (json['owner'] ?? '') as String,
        dueDate: json['due_date'] != null
            ? DateTime.tryParse(json['due_date'] as String)
            : null,
        status: (json['status'] ?? '') as String,
      );

  bool get isDone => status == 'done';
}

class Decision {
  final String id;
  final String description;
  final String decidedBy;
  final String status;
  final DateTime? deadline;

  Decision({
    required this.id,
    required this.description,
    required this.decidedBy,
    required this.status,
    this.deadline,
  });

  factory Decision.fromJson(Map<String, dynamic> json) => Decision(
        id: json['id'].toString(),
        description: (json['description'] ?? '') as String,
        decidedBy: (json['decided_by'] ?? '') as String,
        status: (json['status'] ?? '') as String,
        deadline: json['deadline'] != null
            ? DateTime.tryParse(json['deadline'] as String)
            : null,
      );
}

class Meeting {
  final String id;
  final String title;
  final DateTime? meetingDate;
  final String? summary;
  final String status;
  final String? failureReason;
  final List<ActionItem> actionItems;
  final List<Decision> decisions;
  final int emailDraftCount;

  Meeting({
    required this.id,
    required this.title,
    this.meetingDate,
    this.summary,
    required this.status,
    this.failureReason,
    required this.actionItems,
    required this.decisions,
    required this.emailDraftCount,
  });

  factory Meeting.fromJson(Map<String, dynamic> json) => Meeting(
        id: json['id'].toString(),
        title: (json['title'] ?? '') as String,
        meetingDate: json['meeting_date'] != null
            ? DateTime.tryParse(json['meeting_date'] as String)
            : null,
        summary: json['summary'] as String?,
        status: (json['status'] ?? '') as String,
        failureReason: json['failure_reason'] as String?,
        actionItems: (json['action_items'] as List<dynamic>? ?? const [])
            .map((e) => ActionItem.fromJson(e as Map<String, dynamic>))
            .toList(),
        decisions: (json['decisions'] as List<dynamic>? ?? const [])
            .map((e) => Decision.fromJson(e as Map<String, dynamic>))
            .toList(),
        emailDraftCount: (json['email_drafts'] as List<dynamic>? ?? const []).length,
      );
}
