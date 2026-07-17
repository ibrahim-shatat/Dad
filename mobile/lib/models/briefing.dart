class BriefingItem {
  final String key;
  final String title;
  final String? subtitle;
  final String? detail;
  final String? severity; // low | medium | high
  final bool handled;

  BriefingItem({
    required this.key,
    required this.title,
    this.subtitle,
    this.detail,
    this.severity,
    required this.handled,
  });

  factory BriefingItem.fromJson(Map<String, dynamic> json) => BriefingItem(
        key: (json['key'] ?? '') as String,
        title: (json['title'] ?? '') as String,
        subtitle: json['subtitle'] as String?,
        detail: json['detail'] as String?,
        severity: json['severity'] as String?,
        handled: (json['handled'] ?? false) as bool,
      );
}

class BriefingSection {
  final String id;
  final String label;
  final List<BriefingItem> items;

  BriefingSection({required this.id, required this.label, required this.items});

  factory BriefingSection.fromJson(Map<String, dynamic> json) => BriefingSection(
        id: (json['id'] ?? '') as String,
        label: (json['label'] ?? '') as String,
        items: ((json['items'] as List<dynamic>?) ?? const [])
            .map((e) => BriefingItem.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class Briefing {
  final String? summary;
  final List<String> topPriorities;
  final DateTime? generatedAt;
  final List<BriefingSection> sections;
  final int totalItems;
  final int handledItems;

  Briefing({
    this.summary,
    required this.topPriorities,
    this.generatedAt,
    required this.sections,
    required this.totalItems,
    required this.handledItems,
  });

  factory Briefing.fromJson(Map<String, dynamic> json) => Briefing(
        summary: json['summary'] as String?,
        topPriorities: ((json['top_priorities'] as List<dynamic>?) ?? const [])
            .map((e) => e.toString())
            .toList(),
        generatedAt: json['generated_at'] != null
            ? DateTime.tryParse(json['generated_at'] as String)
            : null,
        sections: ((json['sections'] as List<dynamic>?) ?? const [])
            .map((e) => BriefingSection.fromJson(e as Map<String, dynamic>))
            .toList(),
        totalItems: (json['total_items'] ?? 0) as int,
        handledItems: (json['handled_items'] ?? 0) as int,
      );
}
