class CalendarEvent {
  final String id;
  final String title;
  final String? description;
  final String? location;
  final String? organizer;
  final DateTime startTime;
  final DateTime? endTime;
  final bool isAllDay;
  final List<String> attendees;
  final String? prepBrief;

  CalendarEvent({
    required this.id,
    required this.title,
    this.description,
    this.location,
    this.organizer,
    required this.startTime,
    this.endTime,
    required this.isAllDay,
    required this.attendees,
    this.prepBrief,
  });

  factory CalendarEvent.fromJson(Map<String, dynamic> json) => CalendarEvent(
        id: json['id'].toString(),
        title: (json['title'] ?? '') as String,
        description: json['description'] as String?,
        location: json['location'] as String?,
        organizer: json['organizer'] as String?,
        startTime: DateTime.tryParse((json['start_time'] ?? '') as String) ??
            DateTime.now(),
        endTime: json['end_time'] != null
            ? DateTime.tryParse(json['end_time'] as String)
            : null,
        isAllDay: (json['is_all_day'] ?? false) as bool,
        attendees: ((json['attendees'] as List<dynamic>?) ?? const [])
            .map((e) => e.toString())
            .toList(),
        prepBrief: json['prep_brief'] as String?,
      );
}
