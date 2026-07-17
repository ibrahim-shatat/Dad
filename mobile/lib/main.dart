import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'api/api_client.dart';
import 'screens/home_shell.dart';
import 'screens/login_screen.dart';
import 'state/auth_state.dart';
import 'theme.dart';

void main() {
  final client = ApiClient();
  runApp(
    ChangeNotifierProvider(
      create: (_) => AuthState(client)..restore(),
      child: const DadApp(),
    ),
  );
}

class DadApp extends StatelessWidget {
  const DadApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Dad',
      debugShowCheckedModeBanner: false,
      theme: buildTheme(Brightness.light),
      darkTheme: buildTheme(Brightness.dark),
      home: const _Root(),
    );
  }
}

/// Routes between the login screen and the app based on session status.
class _Root extends StatelessWidget {
  const _Root();

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthState>();
    switch (auth.status) {
      case AuthStatus.unknown:
        return const Scaffold(body: Center(child: CircularProgressIndicator()));
      case AuthStatus.authenticated:
        return const HomeShell();
      case AuthStatus.unauthenticated:
        return const LoginScreen();
    }
  }
}
