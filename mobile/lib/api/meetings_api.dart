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
}
