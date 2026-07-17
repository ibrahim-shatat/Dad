import '../models/meeting.dart';
import 'api_client.dart';

class MeetingsApi {
  final ApiClient _client;
  MeetingsApi(this._client);

  Future<List<Meeting>> list(String token) async {
    final data = await _client.get('/meetings', token: token);
    return (data as List)
        .map((e) => Meeting.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Creates a meeting from notes; the backend queues AI processing (summary,
  /// action items, decisions) which appears once the job runs.
  Future<void> create({
    required String title,
    required String sourceText,
    String? instructions,
    required String token,
  }) {
    return _client.postJson(
      '/meetings',
      {
        'title': title,
        'source_text': sourceText,
        if (instructions != null && instructions.trim().isNotEmpty)
          'instructions': instructions.trim(),
      },
      token: token,
    );
  }
}
