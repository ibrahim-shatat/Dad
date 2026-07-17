import '../models/dashboard_summary.dart';
import 'api_client.dart';

class DashboardApi {
  final ApiClient _client;
  DashboardApi(this._client);

  Future<DashboardSummary> fetch(String token) async {
    final data = await _client.get('/dashboard', token: token);
    return DashboardSummary.fromJson(data as Map<String, dynamic>);
  }
}
