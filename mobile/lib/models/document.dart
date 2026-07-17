class RiskFlag {
  final String category;
  final String description;
  final String severity; // low | medium | high

  RiskFlag({
    required this.category,
    required this.description,
    required this.severity,
  });

  factory RiskFlag.fromJson(Map<String, dynamic> json) => RiskFlag(
        category: (json['category'] ?? '') as String,
        description: (json['description'] ?? '') as String,
        severity: (json['severity'] ?? 'low') as String,
      );
}

class DocumentReview {
  final String executiveSummary;
  final List<RiskFlag> riskFlags;
  final String suggestedRewrite;
  final String modelUsed;

  DocumentReview({
    required this.executiveSummary,
    required this.riskFlags,
    required this.suggestedRewrite,
    required this.modelUsed,
  });

  factory DocumentReview.fromJson(Map<String, dynamic> json) => DocumentReview(
        executiveSummary: (json['executive_summary'] ?? '') as String,
        riskFlags: (json['risk_flags'] as List<dynamic>? ?? const [])
            .map((e) => RiskFlag.fromJson(e as Map<String, dynamic>))
            .toList(),
        suggestedRewrite: (json['suggested_rewrite'] ?? '') as String,
        modelUsed: (json['model_used'] ?? '') as String,
      );
}

class Document {
  final String id;
  final String filename;
  final String mimeType;
  final int fileSize;
  final String status;
  final String? failureReason;
  final DocumentReview? review;

  Document({
    required this.id,
    required this.filename,
    required this.mimeType,
    required this.fileSize,
    required this.status,
    this.failureReason,
    this.review,
  });

  factory Document.fromJson(Map<String, dynamic> json) => Document(
        id: json['id'].toString(),
        filename: (json['filename'] ?? '') as String,
        mimeType: (json['mime_type'] ?? '') as String,
        fileSize: (json['file_size'] ?? 0) as int,
        status: (json['status'] ?? '') as String,
        failureReason: json['failure_reason'] as String?,
        review: json['review'] != null
            ? DocumentReview.fromJson(json['review'] as Map<String, dynamic>)
            : null,
      );

  String get sizeLabel {
    if (fileSize < 1024) return '$fileSize B';
    if (fileSize < 1024 * 1024) return '${(fileSize / 1024).toStringAsFixed(0)} KB';
    return '${(fileSize / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
}
