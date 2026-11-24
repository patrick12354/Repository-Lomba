import 'dart:async';

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/api.dart';
import '../../core/format.dart';
import '../../core/lang.dart';
import '../../core/task.dart';
import '../../core/theme.dart';
import '../../core/widgets.dart';
import '../tasks/moves.dart';

/// One part on one screen: what to do, the numbers behind it, and who has touched it. Deep analysis stays on the website.
class PartScreen extends StatefulWidget {
  const PartScreen({super.key, required this.task, required this.reasons});
  final TaskItem task;
  final List<RejectReason> reasons;
  @override
  State<PartScreen> createState() => _PartScreenState();
}

class _PartScreenState extends State<PartScreen> {
  Json? _part;
  List<Json> _activity = const [];
  String? _error;
  bool _busy = false;

  TaskItem get t => widget.task;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _error = null);
    try {
      final results = await Future.wait([Api.instance.part(t.materialNo), Api.instance.activity(t.id)]);
      if (!mounted) return;
      setState(() {
        _part = results[0] as Json;
        _activity = results[1] as List<Json>;
      });
    } on ApiException catch (e) {
      if (mounted && e.status != 401) setState(() => _error = e.message);
    }
  }

  Future<void> _act(Future<void> Function() call) async {
    setState(() => _busy = true);
    try {
      await call();
      if (mounted) Navigator.of(context).pop();
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() => _busy = false);
      if (e.status != 401) showMessage(context, e.message);
    }
  }

  Future<void> _reject() async {
    final choice = await askRejectReason(context, t, widget.reasons);
    if (choice != null && mounted) unawaited(_act(() => reject(t, choice.reason, choice.note)));
  }

  Future<void> _openWeb() async {
    final ok = await launchUrl(Uri.parse('${Api.base}/parts/${t.materialNo}'), mode: LaunchMode.externalApplication);
    if (!ok && mounted) showMessage(context, tx('Could not open the browser.', 'Browser tidak bisa dibuka.'));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('#${t.materialNo}', style: Theme.of(context).textTheme.titleMedium),
        actions: [
          TextButton.icon(onPressed: _openWeb, icon: const Icon(Icons.open_in_new_rounded, size: 18), label: Text(tx('Open on web', 'Buka di web'))),
        ],
      ),
      body: _error != null ? ErrorRetry(_error!, onRetry: _load) : _body(context),
      bottomNavigationBar: t.actionable || t.canReject ? _actions() : null,
    );
  }

  Widget _actions() {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
        child: Row(children: [
          if (t.canReject) ...[
            Expanded(
              child: OutlinedButton.icon(onPressed: _busy ? null : _reject, icon: const Icon(Icons.close_rounded, color: C.act), label: Text(tx('Reject', 'Tolak'))),
            ),
            const SizedBox(width: 10),
          ],
          if (t.actionable)
            Expanded(
              child: FilledButton.icon(onPressed: _busy ? null : () => _act(() => moveForward(t)), icon: const Icon(Icons.check_rounded), label: Text(t.nextLabel)),
            ),
        ]),
      ),
    );
  }

  Widget _body(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final u = t.urgencyStyle;
    final m = _part?['m'] as Json?;
    final answer = _part?['answer'] as Json?;
    final twins = (_part?['twins'] as List? ?? const []).cast<Json>();
    final ta = answer?['ta'] as Json?;

    return ListView(padding: const EdgeInsets.fromLTRB(16, 4, 16, 20), children: [
      Wrap(spacing: 6, runSpacing: 6, children: [
        Pill(u.label, bg: u.soft, fg: u.ink),
        Pill(t.stageLabel, bg: C.idleSoft, fg: C.idleInk),
      ]),
      const SizedBox(height: 12),
      Text(t.ask, style: text.headlineMedium),
      const SizedBox(height: 6),
      Text(t.description, style: text.titleMedium?.copyWith(fontWeight: FontWeight.w500, color: C.ink2)),
      const SizedBox(height: 16),
      _Panel(children: [
        Row(children: [
          Expanded(child: Stat(tx('On the shelf', 'Di rak'), amount(t.stock, t.unit))),
          Expanded(child: Stat(tx('Needed', 'Dibutuhkan'), amount(t.target, t.unit))),
          Expanded(child: Stat(tx('Value', 'Nilai'), rupiah(t.value))),
        ]),
        if (t.orderBy != null || m != null) ...[
          const SizedBox(height: 14),
          Row(children: [
            Expanded(child: Stat(tx('Order by', 'Pesan paling lambat'), shortDate(t.orderBy), color: (t.daysLeft ?? 1) <= 0 && t.orderBy != null ? C.actInk : null)),
            Expanded(child: Stat(tx('Lead time', 'Waktu tunggu'), m == null ? '–' : tx('${number(m['lt_p90'] as num?)} days', '${number(m['lt_p90'] as num?)} hari'))),
            Expanded(child: Stat(tx('Criticality', 'Kekritisan'), t.criticality)),
          ]),
        ],
      ]),
      if (_part == null) const Padding(padding: EdgeInsets.all(28), child: Center(child: CircularProgressIndicator())),
      if (ta != null) ...[
        const SizedBox(height: 10),
        _Panel(title: tx('For the next turnaround', 'Untuk turnaround berikutnya'), children: [
          Row(children: [
            Expanded(child: Stat(tx('Starts', 'Mulai'), shortDate(ta['date'] as String?))),
            Expanded(child: Stat(tx('Total need', 'Total kebutuhan'), number(ta['total'] as num?))),
            Expanded(child: Stat(tx('Short by', 'Kurang'), number(ta['gap'] as num?), color: ((ta['gap'] as num?) ?? 0) > 0 ? C.actInk : C.readyInk)),
          ]),
        ]),
      ],
      if (m != null && m['main_supplier'] != null) ...[
        const SizedBox(height: 10),
        _Panel(title: tx('Supplier', 'Pemasok'), children: [Text(m['main_supplier'] as String, style: text.titleMedium)]),
      ],
      if (t.machines.isNotEmpty) ...[
        const SizedBox(height: 10),
        _Panel(title: tx('Used on', 'Dipakai di'), children: [
          Wrap(spacing: 6, runSpacing: 6, children: [for (final x in t.machines.take(8)) Pill(x, bg: C.idleSoft, fg: C.idleInk)]),
        ]),
      ],
      if (twins.isNotEmpty) ...[
        const SizedBox(height: 10),
        _Panel(title: tx('Duplicate parts', 'Suku cadang kembar'), children: [
          for (final w in twins.take(4))
            Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(children: [
                const Icon(Icons.swap_horiz_rounded, size: 18, color: C.twin),
                const SizedBox(width: 8),
                Expanded(child: Text(w['description'] as String? ?? '', maxLines: 2, overflow: TextOverflow.ellipsis)),
                const SizedBox(width: 8),
                Text(tx('${number(w['stock'] as num?)} in stock', 'stok ${number(w['stock'] as num?)}'), style: text.bodySmall),
              ]),
            ),
        ]),
      ],
      if (_activity.isNotEmpty) ...[
        const SizedBox(height: 10),
        _Panel(title: tx('What has happened', 'Riwayat'), children: [
          for (final a in _activity.take(6))
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(a['detail'] as String? ?? '', style: text.bodyMedium?.copyWith(color: C.ink)),
                Text('${a['actor'] ?? ''} · ${shortDate(a['at'] as String?)}', style: text.bodySmall),
              ]),
            ),
        ]),
      ],
    ]);
  }
}

class _Panel extends StatelessWidget {
  const _Panel({this.title, required this.children});
  final String? title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: C.panel, borderRadius: BorderRadius.circular(16)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        if (title != null) ...[Text(title!, style: Theme.of(context).textTheme.bodySmall?.copyWith(fontWeight: FontWeight.w600)), const SizedBox(height: 8)],
        ...children,
      ]),
    );
  }
}
