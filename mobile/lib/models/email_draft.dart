class EmailDraft {
  final String id;
  final List<String> toAddresses;
  final List<String> ccAddresses;
  final String subject;
  final String body;
  final String status;

  EmailDraft({
    required this.id,
    required this.toAddresses,
    required this.ccAddresses,
    required this.subject,
    required this.body,
    required this.status,
  });

  factory EmailDraft.fromJson(Map<String, dynamic> json) => EmailDraft(
        id: json['id'].toString(),
        toAddresses: ((json['to_addresses'] as List<dynamic>?) ?? const [])
            .map((e) => e.toString())
            .toList(),
        ccAddresses: ((json['cc_addresses'] as List<dynamic>?) ?? const [])
            .map((e) => e.toString())
            .toList(),
        subject: (json['subject'] ?? '') as String,
        body: (json['body'] ?? '') as String,
        status: (json['status'] ?? '') as String,
      );
}
