import 'package:http_parser/http_parser.dart';

import '../models/document.dart';
import 'api_client.dart';

class DocumentsApi {
  final ApiClient _client;
  DocumentsApi(this._client);

  static const allowedExtensions = ['pdf', 'docx', 'xlsx', 'txt'];

  Future<List<Document>> list(String token) async {
    final data = await _client.get('/documents', token: token);
    return (data as List)
        .map((e) => Document.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Uploads a file for AI review. The backend validates the content type, so we
  /// set it explicitly from the extension rather than sending octet-stream.
  Future<void> upload({
    required String filePath,
    required String filename,
    String? instructions,
    required String token,
  }) {
    final ext = filename.contains('.') ? filename.split('.').last.toLowerCase() : '';
    return _client.uploadFile(
      '/documents',
      filePath: filePath,
      filename: filename,
      contentType: _mediaType(ext),
      fields: {
        if (instructions != null && instructions.trim().isNotEmpty)
          'instructions': instructions.trim(),
      },
      token: token,
    );
  }

  MediaType _mediaType(String ext) {
    switch (ext) {
      case 'pdf':
        return MediaType('application', 'pdf');
      case 'docx':
        return MediaType('application',
            'vnd.openxmlformats-officedocument.wordprocessingml.document');
      case 'xlsx':
        return MediaType('application',
            'vnd.openxmlformats-officedocument.spreadsheetml.sheet');
      case 'txt':
        return MediaType('text', 'plain');
      default:
        return MediaType('application', 'octet-stream');
    }
  }
}
