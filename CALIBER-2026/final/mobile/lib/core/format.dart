import 'package:intl/intl.dart';

import 'lang.dart';

String _clean(num n) => n == n.roundToDouble() ? NumberFormat.decimalPattern('en_US').format(n.round()).replaceAll(',', '.') : n.toStringAsFixed(1).replaceAll('.', ',');

String number(num? n) => n == null ? '–' : _clean(n);

String amount(num? n, String unit) => n == null ? '–' : '${_clean(n)} ${unit.toLowerCase()}';

/// Rupiah in the short form the website and deck use, for example Rp 43,1 M.
String rupiah(num? n) {
  if (n == null) return '–';
  final v = n.abs();
  String short(double x, String suffix) => 'Rp ${x.toStringAsFixed(1).replaceAll('.', ',')} $suffix';
  if (v >= 1e9) return short(n / 1e9, tx('B', 'M'));
  if (v >= 1e6) return short(n / 1e6, tx('M', 'jt'));
  if (v >= 1e3) return short(n / 1e3, tx('K', 'rb'));
  return 'Rp ${n.round()}';
}

const _monthsEn = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const _monthsId = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];

/// Formats an ISO date from the server. A value it cannot read is shown as it came.
String shortDate(String? iso) {
  if (iso == null) return '–';
  final d = DateTime.tryParse(iso);
  if (d == null) return iso;
  final months = Lang.code.value == 'id' ? _monthsId : _monthsEn;
  return '${d.day} ${months[d.month - 1]} ${d.year}';
}

String daysText(int d) {
  if (d < 0) return tx('${-d} ${d == -1 ? 'day' : 'days'} overdue', 'lewat ${-d} hari');
  if (d == 0) return tx('today', 'hari ini');
  return tx('$d ${d == 1 ? 'day' : 'days'} left', '$d hari lagi');
}
