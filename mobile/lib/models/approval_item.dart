class ApprovalItem {
  final String id;
  final String itemType; // email_draft | presentation_export | document_share
  final String previewText;
  final String? requestedByName;
  final String status;
  final DateTime createdAt;

  ApprovalItem({
    required this.id,
    required this.itemType,
    required this.previewText,
    this.requestedByName,
    required this.status,
    required this.createdAt,
  });

  factory ApprovalItem.fromJson(Map<String, dynamic> json) => ApprovalItem(
        id: json['id'].toString(),
        itemType: (json['item_type'] ?? '') as String,
        previewText: (json['preview_text'] ?? '') as String,
        requestedByName: json['requested_by_name'] as String?,
        status: (json['status'] ?? '') as String,
        createdAt:
            DateTime.tryParse((json['created_at'] ?? '') as String) ?? DateTime.now(),
      );

  String get typeLabel {
    switch (itemType) {
      case 'email_draft':
        return 'Email to send';
      case 'presentation_export':
        return 'Presentation export';
      case 'document_share':
        return 'Document to share';
      default:
        return itemType.replaceAll('_', ' ');
    }
  }
}
