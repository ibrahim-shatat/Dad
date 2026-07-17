import 'dart:convert';

import 'package:http/http.dart' as http;

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

  Uri _uri(String path) => Uri.parse('${AppConfig.apiBaseUrl}$path');

  Map<String, String> _headers(String? token, {Map<String, String>? extra}) => {
        'Accept': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
        ...?extra,
      };

  Future<dynamic> get(String path, {String? token}) async {
    final resp = await _http.get(_uri(path), headers: _headers(token));
    return _decode(resp);
  }

  Future<dynamic> postForm(
    String path,
    Map<String, String> fields, {
    String? token,
  }) async {
    final resp = await _http.post(
      _uri(path),
      headers: _headers(
        token,
        extra: {'Content-Type': 'application/x-www-form-urlencoded'},
      ),
      body: fields,
    );
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
