/// One prioritized thing the director should look at now — mirrors the backend
/// `AttentionItem` schema returned by GET /dashboard.
class AttentionItem {
  final String kind; // email | approval | deadline | event
  final String title;
  final String subtitle;
  final String badge;
  final String tone; // urgent | warning | default
  final String link;
  final DateTime? when;

  AttentionItem({
    required this.kind,
    required this.title,
    required this.subtitle,
    required this.badge,
    required this.tone,
    required this.link,
    this.when,
  });

  factory AttentionItem.fromJson(Map<String, dynamic> json) => AttentionItem(
        kind: (json['kind'] ?? '') as String,
        title: (json['title'] ?? '') as String,
        subtitle: (json['subtitle'] ?? '') as String,
        badge: (json['badge'] ?? '') as String,
        tone: (json['tone'] ?? 'default') as String,
        link: (json['link'] ?? '') as String,
        when: json['when'] != null ? DateTime.tryParse(json['when'] as String) : null,
      );
}
