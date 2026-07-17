import '../models/briefing.dart';
import 'api_client.dart';

class BriefingApi {
  final ApiClient _client;
  BriefingApi(this._client);

  Future<Briefing> today(String token) async {
    final data = await _client.get('/briefing/today', token: token);
    return Briefing.fromJson(data as Map<String, dynamic>);
  }

  Future<Briefing> generate(String token) async {
    final data = await _client.postJson('/briefing/generate', {}, token: token);
    return Briefing.fromJson(data as Map<String, dynamic>);
  }

  Future<Briefing> toggle(String key, bool handled, String token) async {
    final data = await _client.postJson(
      '/briefing/items/toggle',
      {'key': key, 'handled': handled},
      token: token,
    );
    return Briefing.fromJson(data as Map<String, dynamic>);
  }
}
