import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/lang.dart';
import '../../core/theme.dart';
import '../tasks/tasks_screen.dart';

class _Account {
  const _Account(this.name, this.email, this.titleEn, this.titleId, this.icon);
  final String name;
  final String email;
  final String titleEn;
  final String titleId;
  final IconData icon;
}

/// The website's demo team. Each person opens to their own work, so a one-tap sign-in is the quickest way to show the roles.
const _demoPassword = 'sparekit2026';
const _accounts = [
  _Account('Nadia Putri', 'nadia@sparekit.demo', 'Inventory Planner', 'Perencana Persediaan', Icons.fact_check_outlined),
  _Account('Bima Santoso', 'bima@sparekit.demo', 'Procurement Buyer', 'Staf Pengadaan', Icons.shopping_cart_outlined),
  _Account('Citra Lestari', 'citra@sparekit.demo', 'Warehouse Lead', 'Kepala Gudang', Icons.warehouse_outlined),
  _Account('Dimas Prakoso', 'dimas@sparekit.demo', 'Maintenance, Rotating', 'Pemeliharaan, Rotating', Icons.settings_outlined),
  _Account('Eka Wulandari', 'eka@sparekit.demo', 'Maintenance, Static', 'Pemeliharaan, Statis', Icons.local_fire_department_outlined),
  _Account('Fajar Hidayat', 'fajar@sparekit.demo', 'Maintenance, Instrument', 'Pemeliharaan, Instrumen', Icons.speed_outlined),
  _Account('Gita Maharani', 'gita@sparekit.demo', 'Finance Lead', 'Kepala Keuangan', Icons.account_balance_outlined),
];

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  String? _busy;
  String? _error;

  Future<void> _signIn(_Account a) async {
    setState(() => (_busy = a.email, _error = null));
    try {
      await Api.instance.login(a.email, _demoPassword);
      if (!mounted) return;
      Navigator.of(context).pushAndRemoveUntil(MaterialPageRoute(builder: (_) => const TasksScreen()), (_) => false);
    } catch (e) {
      if (mounted) setState(() => (_busy = null, _error = e.toString()));
    }
  }

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
          children: [
            Row(children: [
              Container(
                width: 40,
                height: 40,
                alignment: Alignment.center,
                decoration: BoxDecoration(color: C.accent, borderRadius: BorderRadius.circular(11)),
                child: const Icon(Icons.build_rounded, color: Colors.white, size: 21),
              ),
              const SizedBox(width: 10),
              Text('Sparekit', style: text.titleLarge),
              const Spacer(),
              TextButton(onPressed: Lang.toggle, child: Text(tx('Bahasa Indonesia', 'English'))),
            ]),
            const SizedBox(height: 28),
            Text(tx('Spare parts ready before the plant needs them.', 'Suku cadang siap sebelum kilang membutuhkannya.'), style: text.headlineMedium),
            const SizedBox(height: 8),
            Text(tx('The same data as the website. Decide and update from the field.', 'Data yang sama dengan website. Putuskan dan perbarui dari lapangan.'), style: text.bodyMedium),
            const SizedBox(height: 24),
            Text(tx('Sign in as', 'Masuk sebagai'), style: text.titleMedium),
            const SizedBox(height: 10),
            if (_error != null)
              Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(color: C.actSoft, borderRadius: BorderRadius.circular(12)),
                child: Text(_error!, style: const TextStyle(color: C.actInk, fontWeight: FontWeight.w500)),
              ),
            for (final a in _accounts) ...[
              Material(
                color: C.panel,
                borderRadius: BorderRadius.circular(14),
                clipBehavior: Clip.antiAlias,
                child: InkWell(
                  onTap: _busy == null ? () => _signIn(a) : null,
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                    child: Row(children: [
                      Icon(a.icon, color: C.ink2, size: 24),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text(a.name, style: text.titleMedium),
                          Text(tx(a.titleEn, a.titleId), style: text.bodySmall),
                        ]),
                      ),
                      if (_busy == a.email)
                        const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2.2))
                      else
                        const Icon(Icons.chevron_right_rounded, color: C.ink3),
                    ]),
                  ),
                ),
              ),
              const SizedBox(height: 8),
            ],
          ],
        ),
      ),
    );
  }
}
