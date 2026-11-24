import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../core/lang.dart';
import '../../core/task.dart';
import '../../core/theme.dart';
import 'task_card.dart';

/// One decision at a time. Swipe right to approve, left to reject, or use the buttons below.
class DecisionDeck extends StatefulWidget {
  const DecisionDeck({super.key, required this.tasks, required this.onApprove, required this.onReject, required this.onOpen});
  final List<TaskItem> tasks;
  final void Function(TaskItem) onApprove;

  /// Returns true when the rejection went ahead, false when the person backed out.
  final Future<bool> Function(TaskItem) onReject;
  final void Function(TaskItem) onOpen;

  @override
  State<DecisionDeck> createState() => _DecisionDeckState();
}

class _DecisionDeckState extends State<DecisionDeck> with SingleTickerProviderStateMixin {
  late final AnimationController _anim = AnimationController(vsync: this, duration: const Duration(milliseconds: 220));
  Animation<double>? _flight;
  double _dx = 0;

  @override
  void initState() {
    super.initState();
    _anim.addListener(() {
      final f = _flight;
      if (f != null) setState(() => _dx = f.value);
    });
  }

  @override
  void dispose() {
    _anim.dispose();
    super.dispose();
  }

  Future<void> _flyTo(double target) {
    _flight = Tween(begin: _dx, end: target).animate(CurvedAnimation(parent: _anim, curve: Curves.easeOutCubic));
    return _anim.forward(from: 0);
  }

  Future<void> _approve(TaskItem t, double width) async {
    await _flyTo(width * 1.3);
    if (!mounted) return;
    setState(() => _dx = 0);
    widget.onApprove(t);
  }

  Future<void> _reject(TaskItem t, double width) async {
    await _flyTo(-width * 0.5);
    if (!mounted) return;
    final went = await widget.onReject(t);
    if (!mounted) return;
    if (!went) {
      await _flyTo(0);
    }
    if (mounted) setState(() => _dx = 0);
  }

  void _release(TaskItem t, double width, double velocity) {
    final far = _dx.abs() > width * 0.28 || velocity.abs() > 900;
    if (far && (_dx > 0 || (_dx == 0 && velocity > 0))) {
      _approve(t, width);
    } else if (far && t.canReject) {
      _reject(t, width);
    } else {
      _flyTo(0);
    }
  }

  @override
  Widget build(BuildContext context) {
    final top = widget.tasks.first;
    return LayoutBuilder(builder: (context, box) {
      final width = box.maxWidth;
      final tilt = (_dx / width).clamp(-1.0, 1.0);
      return Column(children: [
        Expanded(
          child: Stack(children: [
            if (widget.tasks.length > 1)
              Positioned.fill(
                child: Transform.scale(
                  scale: 0.96 + 0.04 * tilt.abs(),
                  child: IgnorePointer(child: DecisionCard(key: ValueKey('under-${widget.tasks[1].id}'), task: widget.tasks[1])),
                ),
              ),
            Positioned.fill(
              child: GestureDetector(
                onHorizontalDragStart: (_) => _anim.stop(),
                onHorizontalDragUpdate: (d) => setState(() => _dx += d.delta.dx),
                onHorizontalDragEnd: (d) => _release(top, width, d.primaryVelocity ?? 0),
                child: Transform.translate(
                  offset: Offset(_dx, 0),
                  child: Transform.rotate(
                    angle: tilt * math.pi / 24,
                    child: Stack(children: [
                      Positioned.fill(child: DecisionCard(key: ValueKey('top-${top.id}'), task: top, onOpen: () => widget.onOpen(top))),
                      if (tilt > 0.05) _Stamp(text: top.nextLabel, color: C.ready, opacity: (tilt * 3).clamp(0, 1), left: true),
                      if (tilt < -0.05 && top.canReject) _Stamp(text: tx('Reject', 'Tolak'), color: C.act, opacity: (-tilt * 3).clamp(0, 1), left: false),
                    ]),
                  ),
                ),
              ),
            ),
          ]),
        ),
        const SizedBox(height: 14),
        Row(children: [
          if (top.canReject) ...[
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => _reject(top, width),
                icon: const Icon(Icons.close_rounded, color: C.act),
                label: Text(tx('Reject', 'Tolak')),
              ),
            ),
            const SizedBox(width: 10),
          ],
          Expanded(
            child: FilledButton.icon(
              onPressed: () => _approve(top, width),
              icon: const Icon(Icons.check_rounded),
              label: Text(top.nextLabel),
            ),
          ),
        ]),
      ]);
    });
  }
}

class _Stamp extends StatelessWidget {
  const _Stamp({required this.text, required this.color, required this.opacity, required this.left});
  final String text;
  final Color color;
  final double opacity;
  final bool left;

  @override
  Widget build(BuildContext context) {
    return Positioned(
      top: 62,
      left: left ? 20 : null,
      right: left ? null : 20,
      child: Opacity(
        opacity: opacity,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
          decoration: BoxDecoration(color: C.panel, border: Border.all(color: color, width: 2.5), borderRadius: BorderRadius.circular(10)),
          child: Text(text, style: TextStyle(color: color, fontWeight: FontWeight.w800, fontSize: 17)),
        ),
      ),
    );
  }
}
