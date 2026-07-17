import '../models/calendar_event.dart';
import 'api_client.dart';

class CalendarApi {
  final ApiClient _client;
  CalendarApi(this._client);

  Future<List<CalendarEvent>> events(String token) async {
    final data = await _client.get('/calendar/events', token: token);
    return (data as List)
        .map((e) => CalendarEvent.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Queues an AI prep brief for the event (appears after the job runs — refresh).
  Future<void> generatePrep(String eventId, String token) {
    return _client.postJson('/calendar/events/$eventId/prep', {}, token: token);
  }
}
