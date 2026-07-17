/// App-wide configuration. Override the API URL at build time with:
///   flutter run --dart-define=DAD_API_URL=http://10.0.2.2:8000/api/v1
/// (10.0.2.2 is the host machine from the Android emulator.)
class AppConfig {
  static const String apiBaseUrl = String.fromEnvironment(
    'DAD_API_URL',
    defaultValue: 'https://dad-api-rw61.onrender.com/api/v1',
  );
}
