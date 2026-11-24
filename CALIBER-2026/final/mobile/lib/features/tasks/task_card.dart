import 'package:flutter/material.dart';

import '../../core/format.dart';
import '../../core/lang.dart';
import '../../core/task.dart';
import '../../core/theme.dart';
import '../../core/widgets.dart';

/// Everything needed to decide, with no scrolling: what to do, by when, for which machine.
class DecisionCard extends StatelessWidget {
  const DecisionCard({super.key, required this.task, this.onOpen});
  final TaskItem task;
  final VoidCallback? onOpen;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final u = task.urgencyStyle;
    return Material(
      color: C.panel,
      elevation: 2,
      shadowColor: Colors.black26,
      borderRadius: BorderRadius.circular(22),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onOpen,
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Flexible(child: Pill(u.label, bg: u.soft, fg: u.ink)),
              const SizedBox(width: 6),
              Pill(tx('Crit. ${task.criticality}', 'Krit. ${task.criticality}'), bg: C.idleSoft, fg: C.idleInk),
            ]),
            const SizedBox(height: 16),
            Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Icon(task.icon, size: 26, color: u.strong),
              const SizedBox(width: 10),
              Expanded(child: Text(task.ask, style: text.headlineMedium, maxLines: 2, overflow: TextOverflow.ellipsis)),
            ]),
            const SizedBox(height: 10),
            Text(task.description, style: text.titleMedium?.copyWith(fontWeight: FontWeight.w500, color: C.ink2), maxLines: 3, overflow: TextOverflow.ellipsis),
            const SizedBox(height: 4),
            Text('#${task.materialNo}${task.machines.isEmpty ? '' : ' · ${task.machines.take(2).join(', ')}'}', style: text.bodySmall, maxLines: 1, overflow: TextOverflow.ellipsis),
            const Spacer(),
            const Divider(color: C.rail, height: 24),
            Row(children: [
              Expanded(child: Stat(tx('On the shelf', 'Di rak'), amount(task.stock, task.unit))),
              Expanded(child: Stat(tx('Needed', 'Dibutuhkan'), amount(task.target, task.unit))),
            ]),
            const SizedBox(height: 12),
            Row(children: [
              Expanded(child: Stat(tx('Value', 'Nilai'), rupiah(task.value))),
              Expanded(
                child: task.orderBy == null
                    ? Stat(tx('Runs it', 'Pelaksana'), task.owner.split(' ').first)
                    : Stat(tx('Order by', 'Pesan paling lambat'), task.daysLeft == null ? shortDate(task.orderBy) : daysText(task.daysLeft!), color: (task.daysLeft ?? 1) <= 0 ? C.actInk : null),
              ),
            ]),
          ]),
        ),
      ),
    );
  }
}

/// A compact row for lists. With [onNext], it shows the one button that moves the task on.
class TaskTile extends StatelessWidget {
  const TaskTile({super.key, required this.task, this.onOpen, this.onNext});
  final TaskItem task;
  final VoidCallback? onOpen;
  final VoidCallback? onNext;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final u = task.urgencyStyle;
    return Material(
      color: C.panel,
      borderRadius: BorderRadius.circular(16),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onOpen,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Icon(task.icon, size: 20, color: u.strong),
              const SizedBox(width: 8),
              Expanded(child: Text(task.ask, style: text.titleMedium, maxLines: 1, overflow: TextOverflow.ellipsis)),
              const SizedBox(width: 8),
              Text(task.stageLabel, style: text.bodySmall),
            ]),
            const SizedBox(height: 4),
            Text(task.description, style: text.bodyMedium, maxLines: 2, overflow: TextOverflow.ellipsis),
            const SizedBox(height: 8),
            Row(children: [
              Flexible(child: Pill(u.label, bg: u.soft, fg: u.ink)),
              const Spacer(),
              if (onNext == null)
                Flexible(child: Text(task.followLine, style: text.bodySmall, maxLines: 1, overflow: TextOverflow.ellipsis))
              else
                FilledButton(
                  onPressed: onNext,
                  style: FilledButton.styleFrom(minimumSize: const Size(0, 44), padding: const EdgeInsets.symmetric(horizontal: 18)),
                  child: Text(task.nextLabel),
                ),
            ]),
          ]),
        ),
      ),
    );
  }
}
