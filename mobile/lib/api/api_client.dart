import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

import '../config.dart';

/// A failed HTTP response, carrying the backend's `detail` message when present.
class ApiException implements Exception {
  final int statusCode;
  final String message;
  ApiException(this.statusCode, this.message);
  @override
  String toString() => message;
}

/// Thin wrapper over `http` that targets the Dad backend and normalizes errors.
class ApiClient {
  final http.Client _http = http.Client();

  // The API is on Render's free tier, which cold-starts (~30-60s) after idle.
  // Give requests room to wait for that instead of failing as "no connection".
  static const Duration _timeout = Duration(seconds: 75);

  Uri _uri(String path) => Uri.parse('${AppConfig.apiBaseUrl}$path');

  Map<String, String> _headers(String? token, {Map<String, String>? extra}) => {
        'Accept': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
        ...?extra,
      };

  Future<dynamic> get(String path, {String? token}) async {
    final resp =
        await _http.get(_uri(path), headers: _headers(token)).timeout(_timeout);
    return _decode(resp);
  }

  Future<dynamic> postForm(
    String path,
    Map<String, String> fields, {
    String? token,
  }) async {
    final resp = await _http
        .post(
          _uri(path),
          headers: _headers(
            token,
            extra: {'Content-Type': 'application/x-www-form-urlencoded'},
          ),
          body: fields,
        )
        .timeout(_timeout);
    return _decode(resp);
  }

  Future<dynamic> postJson(String path, Object? body, {String? token}) async {
    final resp = await _http
        .post(
          _uri(path),
          headers: _headers(token, extra: {'Content-Type': 'application/json'}),
          body: jsonEncode(body),
        )
        .timeout(_timeout);
    return _decode(resp);
  }

  /// Multipart upload (a single file plus optional form fields).
  Future<dynamic> uploadFile(
    String path, {
    required String filePath,
    required String filename,
    required MediaType contentType,
    Map<String, String> fields = const {},
    String? token,
  }) async {
    final request = http.MultipartRequest('POST', _uri(path));
    if (token != null) request.headers['Authorization'] = 'Bearer $token';
    request.fields.addAll(fields);
    request.files.add(await http.MultipartFile.fromPath(
      'file',
      filePath,
      filename: filename,
      contentType: contentType,
    ));
    final streamed = await request.send().timeout(const Duration(seconds: 90));
    final resp = await http.Response.fromStream(streamed);
    return _decode(resp);
  }

  dynamic _decode(http.Response resp) {
    final ok = resp.statusCode >= 200 && resp.statusCode < 300;
    dynamic data;
    if (resp.body.isNotEmpty) {
      try {
        data = jsonDecode(resp.body);
      } catch (_) {
        data = resp.body;
      }
    }
    if (!ok) {
      final detail = (data is Map && data['detail'] != null)
          ? data['detail'].toString()
          : 'Request failed (${resp.statusCode})';
      throw ApiException(resp.statusCode, detail);
    }
    return data;
  }
}
