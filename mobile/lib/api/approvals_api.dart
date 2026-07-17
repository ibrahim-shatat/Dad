import '../models/approval_item.dart';
import 'api_client.dart';

class ApprovalsApi {
  final ApiClient _client;
  ApprovalsApi(this._client);

  Future<List<ApprovalItem>> pending(String token) async {
    final data = await _client.get('/approvals?status_filter=pending', token: token);
    return (data as List)
        .map((e) => ApprovalItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> approve(String id, String token, {String? note}) {
    return _client.postJson('/approvals/$id/approve', {'note': note}, token: token);
  }

  Future<void> reject(String id, String reason, String token) {
    return _client.postJson('/approvals/$id/reject', {'reason': reason}, token: token);
  }
}
