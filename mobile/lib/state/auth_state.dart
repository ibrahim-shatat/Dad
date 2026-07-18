import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../api/api_client.dart';
import '../api/auth_api.dart';
import '../models/user.dart';
import '../push_service.dart';

enum AuthStatus { unknown, authenticated, unauthenticated }

/// Holds the signed-in session. The access token is kept in the OS secure store
/// (Keychain / Keystore) so it survives app restarts.
class AuthState extends ChangeNotifier {
  final AuthApi _authApi;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  static const _tokenKey = 'dad_access_token';

  AuthState(ApiClient client) : _authApi = AuthApi(client);

  AuthStatus status = AuthStatus.unknown;
  String? token;
  AppUser? user;
  String? error;
  bool busy = false;

  /// Called on launch: restore a saved token and confirm it still works.
  Future<void> restore() async {
    final saved = await _storage.read(key: _tokenKey);
    if (saved == null) {
      status = AuthStatus.unauthenticated;
      notifyListeners();
      return;
    }
    try {
      user = await _authApi.me(saved);
      token = saved;
      status = AuthStatus.authenticated;
      unawaited(PushService.instance.registerForUser(saved));
    } catch (_) {
      await _storage.delete(key: _tokenKey);
      status = AuthStatus.unauthenticated;
    }
    notifyListeners();
  }

  Future<bool> login(String email, String password) async {
    busy = true;
    error = null;
    notifyListeners();
    try {
      final t = await _authApi.login(email.trim(), password);
      user = await _authApi.me(t);
      token = t;
      await _storage.write(key: _tokenKey, value: t);
      status = AuthStatus.authenticated;
      unawaited(PushService.instance.registerForUser(t));
      busy = false;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      error = e.statusCode == 401 ? 'Incorrect email or password.' : e.message;
    } on TimeoutException {
      error =
          'The server is waking up (free hosting). Give it up to a minute, then try again.';
    } catch (e) {
      // Show the real error so connection problems can be diagnosed precisely.
      error = 'Network error: $e';
    }
    busy = false;
    notifyListeners();
    return false;
  }

  Future<void> logout() async {
    await _storage.delete(key: _tokenKey);
    token = null;
    user = null;
    status = AuthStatus.unauthenticated;
    notifyListeners();
  }
}
