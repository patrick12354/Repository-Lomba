import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/lang.dart';
import '../../core/task.dart';
import '../../core/theme.dart';

/// Sends a task to its next stage.
Future<void> moveForward(TaskItem t) => Api.instance.decide(id: t.id, decision: t.nextTo!, materialNo: t.materialNo, action: t.kind);

/// Rejects a task with the reason that teaches the next engine run.
Future<void> reject(TaskItem t, String reason, String? note) => Api.instance.decide(id: t.id, decision: 'rejected', materialNo: t.materialNo, action: t.kind, reason: reason, note: note);

/// Puts a task back where it was before the last move.
Future<void> undo(TaskItem t) {
  if (t.stage == 'todo') return Api.instance.reopen(t.id);
  return Api.instance.decide(id: t.id, decision: t.stage, materialNo: t.materialNo, action: t.kind);
}

class RejectChoice {
  const RejectChoice(this.reason, this.note);
  final String reason;
  final String? note;
}

/// Asks why, with one tap per reason. Returns null when the person backs out.
Future<RejectChoice?> askRejectReason(BuildContext context, TaskItem t, List<RejectReason> reasons) {
  return showModalBottomSheet<RejectChoice>(
    context: context,
    isScrollControlled: true,
    backgroundColor: C.panel,
    showDragHandle: true,
    builder: (_) => _RejectSheet(task: t, reasons: reasons),
  );
}

class _RejectSheet extends StatefulWidget {
  const _RejectSheet({required this.task, required this.reasons});
  final TaskItem task;
  final List<RejectReason> reasons;
  @override
  State<_RejectSheet> createState() => _RejectSheetState();
}

class _RejectSheetState extends State<_RejectSheet> {
  final _note = TextEditingController();

  @override
  void dispose() {
    _note.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Padding(
      padding: EdgeInsets.fromLTRB(20, 0, 20, 16 + MediaQuery.viewInsetsOf(context).bottom),
      child: SingleChildScrollView(
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(tx('Why reject this?', 'Kenapa ditolak?'), style: text.titleLarge),
          const SizedBox(height: 2),
          Text(widget.task.description, style: text.bodySmall, maxLines: 2, overflow: TextOverflow.ellipsis),
          const SizedBox(height: 12),
          TextField(
            controller: _note,
            maxLength: 280,
            decoration: InputDecoration(
              hintText: tx('Add a note (optional)', 'Tambah catatan (opsional)'),
              counterText: '',
              filled: true,
              fillColor: C.ground,
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
            ),
          ),
          const SizedBox(height: 8),
          for (final r in widget.reasons)
            ListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(r.label, style: text.titleMedium),
              subtitle: Text(r.hint, style: text.bodySmall),
              trailing: const Icon(Icons.chevron_right_rounded, color: C.ink3),
              onTap: () {
                final note = _note.text.trim();
                Navigator.of(context).pop(RejectChoice(r.code, note.isEmpty ? null : note));
              },
            ),
        ]),
      ),
    );
  }
}
