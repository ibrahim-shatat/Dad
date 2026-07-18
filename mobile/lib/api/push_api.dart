import 'api_client.dart';

class PushApi {
  final ApiClient _client;
  PushApi(this._client);

  Future<void> registerDevice(String fcmToken, String authToken) {
    return _client.postJson(
      '/push/devices',
      {'token': fcmToken, 'platform': 'android'},
      token: authToken,
    );
  }
}
