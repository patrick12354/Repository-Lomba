import 'package:flutter/material.dart';

import 'core/api.dart';
import 'core/lang.dart';
import 'core/theme.dart';
import 'features/login/login_screen.dart';
import 'features/tasks/tasks_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Lang.load();
  await Api.instance.load();
  runApp(const SparekitApp());
}

class SparekitApp extends StatefulWidget {
  const SparekitApp({super.key});
  @override
  State<SparekitApp> createState() => _SparekitAppState();
}

class _SparekitAppState extends State<SparekitApp> {
  final _nav = GlobalKey<NavigatorState>();

  @override
  void initState() {
    super.initState();
    Api.instance.signedOut.addListener(_toLogin);
  }

  @override
  void dispose() {
    Api.instance.signedOut.removeListener(_toLogin);
    super.dispose();
  }

  void _toLogin() => _nav.currentState?.pushAndRemoveUntil(MaterialPageRoute(builder: (_) => const LoginScreen()), (_) => false);

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: Lang.code,
      builder: (context, _, _) => MaterialApp(
        navigatorKey: _nav,
        title: 'Sparekit',
        debugShowCheckedModeBanner: false,
        theme: buildTheme(),
        home: Api.instance.hasSession ? const TasksScreen() : const LoginScreen(),
        // Larger system text is respected, but capped so cards hold together on a 360 dp phone.
        builder: (context, child) {
          final mq = MediaQuery.of(context);
          return MediaQuery(data: mq.copyWith(textScaler: mq.textScaler.clamp(maxScaleFactor: 1.3)), child: child!);
        },
      ),
    );
  }
}
