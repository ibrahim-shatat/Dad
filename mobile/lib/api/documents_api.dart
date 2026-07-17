import '../models/document.dart';
import 'api_client.dart';

class DocumentsApi {
  final ApiClient _client;
  DocumentsApi(this._client);

  Future<List<Document>> list(String token) async {
    final data = await _client.get('/documents', token: token);
    return (data as List)
        .map((e) => Document.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
