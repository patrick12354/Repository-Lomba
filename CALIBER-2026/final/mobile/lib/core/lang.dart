import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// The same `t("English", "Indonesia")` habit as the website: both wordings sit side by side.
class Lang {
  Lang._();
  static const _key = 'sk_lang';
  static final code = ValueNotifier<String>('id');

  static Future<void> load() async {
    try {
      final saved = (await SharedPreferences.getInstance()).getString(_key);
      if (saved == 'en' || saved == 'id') code.value = saved!;
    } catch (_) {
      // Keep the default.
    }
  }

  static Future<void> toggle() async {
    code.value = code.value == 'id' ? 'en' : 'id';
    try {
      await (await SharedPreferences.getInstance()).setString(_key, code.value);
    } catch (_) {
      // The choice still holds until the app closes.
    }
  }
}

String tx(String en, String id) => Lang.code.value == 'id' ? id : en;
