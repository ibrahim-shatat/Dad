import '../models/user.dart';
import 'api_client.dart';

class AuthApi {
  final ApiClient _client;
  AuthApi(this._client);

  /// OAuth2 password form: fields are `username` (the email) and `password`.
  Future<String> login(String email, String password) async {
    final data = await _client.postForm('/auth/login', {
      'username': email,
      'password': password,
    });
    return data['access_token'] as String;
  }

  Future<AppUser> me(String token) async {
    final data = await _client.get('/users/me', token: token);
    return AppUser.fromJson(data as Map<String, dynamic>);
  }
}
