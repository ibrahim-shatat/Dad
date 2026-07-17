class ChatSource {
  final String label;
  final String link;

  ChatSource({required this.label, required this.link});

  factory ChatSource.fromJson(Map<String, dynamic> json) => ChatSource(
        label: (json['label'] ?? '') as String,
        link: (json['link'] ?? '') as String,
      );
}

class ChatResponse {
  final String answer;
  final List<ChatSource> sources;

  ChatResponse({required this.answer, required this.sources});

  factory ChatResponse.fromJson(Map<String, dynamic> json) => ChatResponse(
        answer: (json['answer'] ?? '') as String,
        sources: ((json['sources'] as List<dynamic>?) ?? const [])
            .map((e) => ChatSource.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}
