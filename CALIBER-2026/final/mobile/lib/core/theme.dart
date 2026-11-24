import 'package:flutter/material.dart';

/// Colours carry the website's meaning (red = act, amber = plan, teal = twin), so people moving between the two read them the same way.
class C {
  static const ground = Color(0xFFF5F4F1);
  static const panel = Color(0xFFFFFFFF);
  static const rail = Color(0xFFE9E5DE);
  static const ink = Color(0xFF16171A);
  static const ink2 = Color(0xFF47474A);
  static const ink3 = Color(0xFF6F6F73);
  static const accent = Color(0xFFD9480F);
  static const act = Color(0xFFD8402A);
  static const actSoft = Color(0xFFFCEBE7);
  static const actInk = Color(0xFFA52C1B);
  static const plan = Color(0xFFE39A12);
  static const planSoft = Color(0xFFFDF3DA);
  static const planInk = Color(0xFF855A00);
  static const watch = Color(0xFF3B6FD4);
  static const watchSoft = Color(0xFFE9EFFC);
  static const watchInk = Color(0xFF2650A8);
  static const ready = Color(0xFF2A9A5A);
  static const readySoft = Color(0xFFE4F4EA);
  static const readyInk = Color(0xFF177340);
  static const excess = Color(0xFF7C4DDB);
  static const excessSoft = Color(0xFFF0EAFD);
  static const excessInk = Color(0xFF5B33B0);
  static const idleSoft = Color(0xFFEFEDEA);
  static const idleInk = Color(0xFF55565B);
  static const twin = Color(0xFF0E9384);
  static const twinSoft = Color(0xFFDFF3EF);
  static const twinInk = Color(0xFF0B6F64);
}

ThemeData buildTheme() {
  final scheme = ColorScheme.fromSeed(seedColor: C.accent, surface: C.ground).copyWith(primary: C.ink, onPrimary: Colors.white, error: C.act);
  return ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    scaffoldBackgroundColor: C.ground,
    appBarTheme: const AppBarTheme(backgroundColor: C.ground, foregroundColor: C.ink, elevation: 0, scrolledUnderElevation: 0),
    textTheme: const TextTheme(
      headlineMedium: TextStyle(fontSize: 26, fontWeight: FontWeight.w700, height: 1.15, letterSpacing: -0.4, color: C.ink),
      titleLarge: TextStyle(fontSize: 20, fontWeight: FontWeight.w700, height: 1.25, letterSpacing: -0.2, color: C.ink),
      titleMedium: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, height: 1.3, color: C.ink),
      bodyMedium: TextStyle(fontSize: 14, height: 1.4, color: C.ink2),
      bodySmall: TextStyle(fontSize: 12.5, height: 1.35, color: C.ink3),
      labelLarge: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(minimumSize: const Size(0, 52), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14))),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        minimumSize: const Size(0, 52),
        foregroundColor: C.ink,
        side: const BorderSide(color: C.rail, width: 1.5),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      ),
    ),
    snackBarTheme: const SnackBarThemeData(behavior: SnackBarBehavior.floating, backgroundColor: C.ink),
  );
}
