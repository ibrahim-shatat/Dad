import '../models/email_account.dart';
import '../models/email_draft.dart';
import '../models/email_message.dart';
import 'api_client.dart';

class EmailApi {
  final ApiClient _client;
  EmailApi(this._client);

  Future<List<EmailAccount>> accounts(String token) async {
    final data = await _client.get('/email/accounts', token: token);
    return (data as List)
        .map((e) => EmailAccount.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<EmailMessage>> messages(String token) async {
    final data = await _client.get('/email/messages', token: token);
    return (data as List)
        .map((e) => EmailMessage.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<EmailDraft> draft(String draftId, String token) async {
    final data = await _client.get('/email/drafts/$draftId', token: token);
    return EmailDraft.fromJson(data as Map<String, dynamic>);
  }

  /// Queues an AI reply draft that lands in the approval queue (never sends directly).
  Future<void> draftReply(String messageId, String? instructions, String token) {
    return _client.postJson(
      '/email/messages/$messageId/draft-reply',
      {'instructions': instructions},
      token: token,
    );
  }
}
