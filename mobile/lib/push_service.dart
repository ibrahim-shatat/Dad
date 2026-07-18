import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

import 'api/api_client.dart';
import 'api/push_api.dart';

/// Native push (Firebase Cloud Messaging). Entirely optional: the Firebase config
/// is passed at build time via --dart-define (the CI extracts it from the
/// GOOGLE_SERVICES_JSON secret). When it's absent, every method here is a no-op,
/// so the app builds and runs identically without push.
class PushService {
  PushService._();
  static final PushService instance = PushService._();

  bool _initialized = false;
  String? _lastRegisteredToken;

  static const _apiKey = String.fromEnvironment('FIREBASE_API_KEY');
  static const _appId = String.fromEnvironment('FIREBASE_APP_ID');
  static const _senderId = String.fromEnvironment('FIREBASE_SENDER_ID');
  static const _projectId = String.fromEnvironment('FIREBASE_PROJECT_ID');

  bool get configured =>
      _apiKey.isNotEmpty &&
      _appId.isNotEmpty &&
      _senderId.isNotEmpty &&
      _projectId.isNotEmpty;

  /// Initialize Firebase (once), ask permission, and register this device's FCM
  /// token with the backend for the signed-in user. Best-effort — never throws.
  Future<void> registerForUser(String authToken) async {
    if (!configured) return;
    try {
      if (!_initialized) {
        await Firebase.initializeApp(
          options: const FirebaseOptions(
            apiKey: _apiKey,
            appId: _appId,
            messagingSenderId: _senderId,
            projectId: _projectId,
          ),
        );
        _initialized = true;
      }

      final messaging = FirebaseMessaging.instance;
      await messaging.requestPermission();

      final token = await messaging.getToken();
      if (token != null && token != _lastRegisteredToken) {
        _lastRegisteredToken = token;
        await PushApi(ApiClient()).registerDevice(token, authToken);
      }

      // Re-register if Firebase rotates the token while signed in.
      messaging.onTokenRefresh.listen((refreshed) async {
        _lastRegisteredToken = refreshed;
        try {
          await PushApi(ApiClient()).registerDevice(refreshed, authToken);
        } catch (_) {}
      });
    } catch (_) {
      // Push is a bonus; a failure here must never affect sign-in or the app.
    }
  }
}
