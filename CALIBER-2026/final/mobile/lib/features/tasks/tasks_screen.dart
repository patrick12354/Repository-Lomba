import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/lang.dart';
import '../../core/task.dart';
import '../../core/theme.dart';
import '../../core/widgets.dart';
import '../part/part_screen.dart';
import 'decision_deck.dart';
import 'moves.dart';
import 'task_card.dart';

/// The home of the app: what this person has to do now. Refreshes itself so moves made on the website appear here too.
class TasksScreen extends StatefulWidget {
  const TasksScreen({super.key});
  @override
  State<TasksScreen> createState() => _TasksScreenState();
}

class _TasksScreenState extends State<TasksScreen> with WidgetsBindingObserver {
  static const _pollEvery = Duration(seconds: 20);

  Inbox? _inbox;
  String? _error;
  bool _following = false;
  bool _listMode = false;
  Timer? _poll;

  /// Tasks moved here and not yet confirmed. A refresh that arrives meanwhile must not bring them back.
  final _pending = <String>{};

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _load();
    _poll = Timer.periodic(_pollEvery, (_) => _load(quiet: true));
    Lang.code.addListener(_load);
  }

  @override
  void dispose() {
    Lang.code.removeListener(_load);
    WidgetsBinding.instance.removeObserver(this);
    _poll?.cancel();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) _load(quiet: true);
  }

  Future<void> _load({bool quiet = false}) async {
    try {
      final inbox = Inbox(await Api.instance.inbox());
      if (mounted) setState(() => (_inbox = inbox, _error = null));
    } on ApiException catch (e) {
      if (e.status == 401 || !mounted) return; // The app is already on its way back to the login screen.
      // A background refresh keeps the last good list on screen rather than blanking it on a weak signal.
      if (!quiet || _inbox == null) setState(() => _error = e.message);
    }
  }

  List<TaskItem> get _act => (_inbox?.act ?? const <TaskItem>[]).where((t) => !_pending.contains(t.id)).toList();

  Future<void> _send(TaskItem t, Future<void> Function() call, String done) async {
    setState(() => _pending.add(t.id));
    try {
      await call();
      if (!mounted) return;
      await _load(quiet: true);
      if (!mounted) return;
      setState(() => _pending.remove(t.id));
      showMessage(context, done, actionLabel: tx('Undo', 'Batalkan'), onAction: () => _undo(t));
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() => _pending.remove(t.id));
      if (e.status != 401) showMessage(context, e.message);
    }
  }

  Future<void> _undo(TaskItem t) async {
    try {
      await undo(t);
      await _load(quiet: true);
    } on ApiException catch (e) {
      if (mounted && e.status != 401) showMessage(context, e.message);
    }
  }

  void _approve(TaskItem t) => _send(t, () => moveForward(t), t.movedLabel);

  Future<bool> _reject(TaskItem t) async {
    final choice = await askRejectReason(context, t, _inbox!.reasons);
    if (choice == null || !mounted) return false;
    unawaited(_send(t, () => reject(t, choice.reason, choice.note), tx('Rejected. The next run learns from this.', 'Ditolak. Perhitungan berikutnya belajar dari ini.')));
    return true;
  }

  Future<void> _open(TaskItem t) async {
    await Navigator.of(context).push(MaterialPageRoute(builder: (_) => PartScreen(task: t, reasons: _inbox?.reasons ?? const [])));
    if (mounted) unawaited(_load(quiet: true));
  }

  void _menu() {
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: C.panel,
      showDragHandle: true,
      builder: (sheet) => SafeArea(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          ListTile(title: Text(_inbox?.name ?? ''), subtitle: Text(_inbox?.title ?? '')),
          const Divider(color: C.rail),
          ListTile(
            leading: const Icon(Icons.translate_rounded),
            title: Text(tx('Bahasa Indonesia', 'English')),
            onTap: () {
              Navigator.of(sheet).pop();
              Lang.toggle();
            },
          ),
          ListTile(
            leading: const Icon(Icons.logout_rounded),
            title: Text(tx('Sign out', 'Keluar')),
            onTap: () {
              Navigator.of(sheet).pop();
              Api.instance.logout();
            },
          ),
        ]),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final inbox = _inbox;
    return Scaffold(
      body: SafeArea(
        child: inbox == null
            ? (_error != null ? ErrorRetry(_error!, onRetry: _load) : const Center(child: CircularProgressIndicator()))
            : Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 14),
                child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                  _Header(inbox: inbox, left: _act.length + (inbox.actTotal - inbox.act.length), onMenu: _menu),
                  const SizedBox(height: 12),
                  _Tabs(
                    following: _following,
                    act: _act.length + (inbox.actTotal - inbox.act.length),
                    follow: inbox.followTotal,
                    onChange: (v) => setState(() => _following = v),
                  ),
                  const SizedBox(height: 12),
                  Expanded(child: _following ? _followList(inbox) : _actView(inbox)),
                ]),
              ),
      ),
    );
  }

  /// The planner decides many things in a row, so they get the deck. Everyone else runs what is decided, so they get a list.
  Widget _actView(Inbox inbox) {
    final items = _act;
    if (items.isEmpty) return _Empty(onRefresh: _load);
    if (inbox.role == 'planner' && !_listMode) {
      return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Expanded(child: DecisionDeck(tasks: items, onApprove: _approve, onReject: _reject, onOpen: _open)),
        Center(
          child: TextButton.icon(
            onPressed: () => setState(() => _listMode = true),
            icon: const Icon(Icons.view_list_rounded, size: 18),
            label: Text(tx('See as a list', 'Lihat sebagai daftar')),
          ),
        ),
      ]);
    }
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      Expanded(
        child: RefreshIndicator(
          onRefresh: _load,
          child: ListView.separated(
            itemCount: items.length + (inbox.actTotal > inbox.act.length ? 1 : 0),
            separatorBuilder: (_, _) => const SizedBox(height: 8),
            itemBuilder: (_, i) {
              if (i == items.length) return _MoreOnWeb(shown: inbox.act.length, total: inbox.actTotal);
              final t = items[i];
              return TaskTile(key: ValueKey(t.id), task: t, onOpen: () => _open(t), onNext: () => _approve(t));
            },
          ),
        ),
      ),
      if (inbox.role == 'planner')
        Center(
          child: TextButton.icon(
            onPressed: () => setState(() => _listMode = false),
            icon: const Icon(Icons.style_rounded, size: 18),
            label: Text(tx('One at a time', 'Satu per satu')),
          ),
        ),
    ]);
  }

  Widget _followList(Inbox inbox) {
    if (inbox.follow.isEmpty) {
      return _Empty(onRefresh: _load, message: tx('Nothing to follow right now.', 'Belum ada yang dipantau.'));
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.separated(
        itemCount: inbox.follow.length + (inbox.followTotal > inbox.follow.length ? 1 : 0),
        separatorBuilder: (_, _) => const SizedBox(height: 8),
        itemBuilder: (_, i) => i == inbox.follow.length
            ? _MoreOnWeb(shown: inbox.follow.length, total: inbox.followTotal)
            : TaskTile(key: ValueKey(inbox.follow[i].id), task: inbox.follow[i], onOpen: () => _open(inbox.follow[i])),
      ),
    );
  }
}

class _MoreOnWeb extends StatelessWidget {
  const _MoreOnWeb({required this.shown, required this.total});
  final int shown;
  final int total;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(14),
      child: Text(
        tx('Showing the $shown most urgent of $total. The full list is on the website.', 'Menampilkan $shown paling mendesak dari $total. Daftar lengkapnya ada di website.'),
        textAlign: TextAlign.center,
        style: Theme.of(context).textTheme.bodySmall,
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.inbox, required this.left, required this.onMenu});
  final Inbox inbox;
  final int left;
  final VoidCallback onMenu;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    // The urgent count leads: a planner's full list runs to thousands, and that number helps no one decide what to do next.
    final title = inbox.urgent > 0
        ? tx('${inbox.firstName}, ${inbox.urgent} urgent', '${inbox.firstName}, ${inbox.urgent} mendesak')
        : tx('Hi ${inbox.firstName}, $left to do', 'Hai ${inbox.firstName}, $left tugas');
    final line = inbox.late > 0
        ? tx('${inbox.late} too late for a normal order', '${inbox.late} terlambat untuk pesanan biasa')
        : inbox.urgent > 0
            ? tx('To do this week', 'Harus dikerjakan minggu ini')
            : tx('Nothing urgent', 'Tidak ada yang mendesak');
    return Row(children: [
      Expanded(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(title, style: text.titleLarge, maxLines: 1, overflow: TextOverflow.ellipsis),
          const SizedBox(height: 1),
          Text(line, style: text.bodyMedium?.copyWith(color: inbox.urgent > 0 ? C.actInk : C.ink3, fontWeight: FontWeight.w500), maxLines: 1, overflow: TextOverflow.ellipsis),
        ]),
      ),
      IconButton(
        onPressed: onMenu,
        tooltip: tx('Account', 'Akun'),
        icon: CircleAvatar(radius: 19, backgroundColor: C.ink, child: Text(inbox.name[0], style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700))),
      ),
    ]);
  }
}

class _Tabs extends StatelessWidget {
  const _Tabs({required this.following, required this.act, required this.follow, required this.onChange});
  final bool following;
  final int act;
  final int follow;
  final ValueChanged<bool> onChange;

  @override
  Widget build(BuildContext context) {
    return SegmentedButton<bool>(
      showSelectedIcon: false,
      style: SegmentedButton.styleFrom(selectedBackgroundColor: C.ink, selectedForegroundColor: Colors.white, side: const BorderSide(color: C.rail)),
      segments: [
        ButtonSegment(value: false, label: Text(tx('For me ($act)', 'Untuk saya ($act)'))),
        ButtonSegment(value: true, label: Text(tx('Following ($follow)', 'Dipantau ($follow)'))),
      ],
      selected: {following},
      onSelectionChanged: (s) => onChange(s.first),
    );
  }
}

class _Empty extends StatelessWidget {
  const _Empty({required this.onRefresh, this.message});
  final Future<void> Function() onRefresh;
  final String? message;

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: onRefresh,
      child: ListView(children: [
        const SizedBox(height: 110),
        const Icon(Icons.task_alt_rounded, size: 52, color: C.ready),
        const SizedBox(height: 12),
        Text(message ?? tx('All clear. Nothing is waiting on you.', 'Beres. Tidak ada yang menunggu Anda.'), textAlign: TextAlign.center, style: Theme.of(context).textTheme.titleMedium),
      ]),
    );
  }
}
