import '../models/chat.dart';
import 'api_client.dart';

class AssistantApi {
  final ApiClient _client;
  AssistantApi(this._client);

  Future<ChatResponse> ask(String question, String token) async {
    final data = await _client.postJson(
      '/search/chat',
      {'question': question},
      token: token,
    );
    return ChatResponse.fromJson(data as Map<String, dynamic>);
  }
}
