import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

import 'lang.dart';

typedef Json = Map<String, dynamic>;

class ApiException implements Exception {
  ApiException(this.message, {this.status});
  final String message;
  final int? status;
  @override
  String toString() => message;
}

/// Talks to the same Next.js app as the website, so a move made here shows up there.
/// Debug builds use the emulator's route to the local dev server. Override with `--dart-define=SPAREKIT_API=https://...`.
class Api {
  Api._();
  static final Api instance = Api._();

  static const _override = String.fromEnvironment('SPAREKIT_API');
  static const _production = 'https://app-raphaeladikaras-projects.vercel.app';
  static const _sessionKey = 'sk_session';
  static const _timeout = Duration(seconds: 20);
  static const inboxLimit = 60;

  static String get base => _override.isNotEmpty ? _override : (kDebugMode ? 'http://10.0.2.2:3100' : _production);

  final _storage = const FlutterSecureStorage();
  final _client = http.Client();
  String? _session;

  /// Fires when the server stops accepting the session, so the app can return to the login screen.
  final signedOut = ValueNotifier<int>(0);

  bool get hasSession => _session != null;

  Future<void> load() async {
    try {
      _session = await _storage.read(key: _sessionKey);
    } catch (_) {
      _session = null;
    }
  }

  Future<void> login(String email, String password) async {
    final res = await _send(() => _client.post(_uri('/api/auth/login'), headers: _headers(), body: jsonEncode({'login': email, 'password': password})));
    _check(res, signOutOn401: false);
    final session = sessionFrom(res.headers['set-cookie']);
    if (session == null) throw ApiException(tx('The server did not start a session.', 'Server tidak memulai sesi.'));
    _session = session;
    await _storage.write(key: _sessionKey, value: session);
  }

  Future<void> logout() async {
    try {
      await _client.post(_uri('/api/auth/logout'), headers: _headers()).timeout(const Duration(seconds: 5));
    } catch (_) {
      // Signing out on this phone still has to work without a signal.
    }
    await _forget();
  }

  /// The most urgent tasks only: the list refreshes often, and the planner alone has thousands.
  Future<Json> inbox() => _getJson('/api/mobile/inbox?limit=$inboxLimit');
  Future<Json> part(int materialNo) => _getJson('/api/parts/$materialNo');

  Future<List<Json>> activity(String id) async {
    final body = await _getJson('/api/activity?id=${Uri.encodeQueryComponent(id)}');
    return (body['rows'] as List).cast<Json>();
  }

  /// Moves a task forward or rejects it. The server applies the same rule as the website's board.
  Future<void> decide({required String id, required String decision, int? materialNo, String? action, String? reason, String? note}) async {
    final res = await _send(() => _client.post(
          _uri('/api/decisions'),
          headers: _headers(),
          body: jsonEncode({
            'id': id,
            'decision': decision,
            'material_no': materialNo,
            'action': action,
            'reason': reason,
            'reason_source': reason == null ? null : 'planner',
            'note': note,
          }),
        ));
    _check(res);
  }

  /// Back to To decide.
  Future<void> reopen(String id) async {
    final res = await _send(() => _client.delete(_uri('/api/decisions?id=${Uri.encodeQueryComponent(id)}'), headers: _headers()));
    _check(res);
  }

  /// Reads the signed value out of a `Set-Cookie` header. Other cookies in the header are ignored.
  @visibleForTesting
  static String? sessionFrom(String? header) {
    if (header == null) return null;
    return RegExp(r'(?:^|[,\s])sk_session=([^;,\s]+)').firstMatch(header)?.group(1);
  }

  Uri _uri(String path) => Uri.parse('$base$path');

  Map<String, String> _headers() => {
        'content-type': 'application/json',
        'cookie': ['sk_lang=${Lang.code.value}', if (_session != null) 'sk_session=$_session'].join('; '),
      };

  Future<Json> _getJson(String path) async {
    final res = await _send(() => _client.get(_uri(path), headers: _headers()));
    _check(res);
    return jsonDecode(utf8.decode(res.bodyBytes)) as Json;
  }

  Future<http.Response> _send(Future<http.Response> Function() call) async {
    try {
      return await call().timeout(_timeout);
    } on TimeoutException {
      throw ApiException(tx('The server took too long. Try again.', 'Server terlalu lama merespons. Coba lagi.'));
    } on http.ClientException {
      throw ApiException(tx('No connection to the server.', 'Tidak ada koneksi ke server.'));
    } catch (e) {
      // dart:io's SocketException and HandshakeException land here.
      throw ApiException(tx('No connection to the server.', 'Tidak ada koneksi ke server.'));
    }
  }

  void _check(http.Response res, {bool signOutOn401 = true}) {
    if (res.statusCode >= 200 && res.statusCode < 300) return;
    if (res.statusCode == 401 && signOutOn401) {
      unawaited(_forget());
      throw ApiException(tx('Your session ended. Sign in again.', 'Sesi Anda berakhir. Silakan masuk lagi.'), status: 401);
    }
    var message = tx('The server could not do that (${res.statusCode}).', 'Server tidak bisa memprosesnya (${res.statusCode}).');
    try {
      final body = jsonDecode(utf8.decode(res.bodyBytes));
      if (body is Map && body['error'] is String) message = body['error'] as String;
    } catch (_) {
      // Not JSON, for example a hosting login page: keep the general message.
    }
    throw ApiException(message, status: res.statusCode);
  }

  Future<void> _forget() async {
    _session = null;
    try {
      await _storage.delete(key: _sessionKey);
    } catch (_) {
      // Nothing stored, or the keystore is unavailable: the session is already gone from memory.
    }
    signedOut.value++;
  }
}
