import 'package:flutter/material.dart';

import 'api.dart';
import 'format.dart';
import 'lang.dart';
import 'theme.dart';

/// One row of `/api/mobile/inbox`.
class TaskItem {
  TaskItem(this.raw);
  final Json raw;

  String get id => raw['id'] as String;
  int get materialNo => (raw['material_no'] as num).toInt();
  String get description => raw['description'] as String? ?? '';
  String get unit => raw['unit'] as String? ?? '';
  String get criticality => raw['criticality'] as String? ?? '';
  String get kind => raw['kind'] as String;
  String get urgency => raw['urgency'] as String;
  num get stock => raw['stock'] as num? ?? 0;
  num get target => raw['target'] as num? ?? 0;
  num get qty => raw['qty'] as num? ?? 0;
  String? get orderBy => raw['order_by'] as String?;
  int? get daysLeft => (raw['days_left'] as num?)?.toInt();
  num? get value => raw['value'] as num?;
  List<String> get machines => (raw['machines'] as List? ?? const []).cast<String>();
  Json? get twin => raw['twin'] as Json?;
  String get owner => raw['owner'] as String? ?? '';
  String get stage => raw['stage'] as String;
  String? get nextTo => raw['next_to'] as String?;
  bool get actionable => raw['actionable'] == true;
  bool get canReject => raw['can_reject'] == true;

  /// What this task asks for, in one short line.
  String get ask => switch (kind) {
        'expedite' => tx('Rush ${amount(qty, unit)}', 'Percepat ${amount(qty, unit)}'),
        'order' => tx('Order ${amount(qty, unit)}', 'Pesan ${amount(qty, unit)}'),
        'twin' => tx('Move ${amount(qty, unit)} from the twin', 'Pindahkan ${amount(qty, unit)} dari kembaran'),
        'reduce' => tx('Stop buying, ${amount(qty, unit)} extra', 'Hentikan pembelian, lebih ${amount(qty, unit)}'),
        'dispose' => tx('Check if still needed', 'Periksa apakah masih diperlukan'),
        _ => tx('Keep an eye on', 'Pantau'),
      };

  /// Words for the one button that moves this task on.
  String get nextLabel => switch (nextTo) {
        'approved' => kind == 'watch' ? tx('Keep watching', 'Terus pantau') : tx('Approve', 'Setujui'),
        'in_progress' => tx('Start', 'Mulai'),
        'done' => tx('Mark done', 'Tandai selesai'),
        _ => '',
      };

  /// What the person sees after moving it, so they know it worked.
  String get movedLabel => switch (nextTo) {
        'approved' => tx('Approved. $owner runs it next.', 'Disetujui. Berikutnya dikerjakan $owner.'),
        'in_progress' => tx('Started.', 'Dimulai.'),
        'done' => tx('Marked done.', 'Ditandai selesai.'),
        _ => '',
      };

  String get stageLabel => switch (stage) {
        'approved' => tx('Approved', 'Disetujui'),
        'in_progress' => tx('In progress', 'Sedang berjalan'),
        'done' => tx('Done', 'Selesai'),
        'rejected' => tx('Rejected', 'Ditolak'),
        _ => tx('To decide', 'Perlu diputuskan'),
      };

  /// Waiting on whom, for tasks this person only follows.
  String get followLine => stage == 'todo' && kind != 'watch' ? tx('Waiting for the planner', 'Menunggu perencana') : tx('With $owner', 'Di tangan $owner');

  UrgencyStyle get urgencyStyle => switch (urgency) {
        'late' => UrgencyStyle(tx('Too late for a normal order', 'Terlambat untuk pesanan biasa'), C.actSoft, C.actInk, C.act),
        'now' => UrgencyStyle(tx('Order this week', 'Pesan minggu ini'), C.actSoft, C.actInk, C.act),
        'month' => UrgencyStyle(tx('Order this month', 'Pesan bulan ini'), C.planSoft, C.planInk, C.plan),
        'later' => UrgencyStyle(tx('Later', 'Nanti'), C.watchSoft, C.watchInk, C.watch),
        _ => UrgencyStyle(tx('No rush', 'Tidak mendesak'), C.idleSoft, C.idleInk, C.idleInk),
      };

  IconData get icon => switch (kind) {
        'expedite' => Icons.bolt_rounded,
        'order' => Icons.shopping_cart_outlined,
        'twin' => Icons.swap_horiz_rounded,
        'reduce' => Icons.inventory_2_outlined,
        'dispose' => Icons.archive_outlined,
        _ => Icons.visibility_outlined,
      };
}

class UrgencyStyle {
  const UrgencyStyle(this.label, this.soft, this.ink, this.strong);
  final String label;
  final Color soft;
  final Color ink;
  final Color strong;
}

class RejectReason {
  const RejectReason(this.code, this.label, this.hint);
  final String code;
  final String label;
  final String hint;
}

/// The whole inbox response.
class Inbox {
  Inbox(Json j)
      : name = (j['me'] as Json)['name'] as String,
        title = (j['me'] as Json)['title'] as String,
        role = (j['me'] as Json)['role'] as String,
        actTotal = ((j['counts'] as Json)['act'] as num).toInt(),
        followTotal = ((j['counts'] as Json)['follow'] as num).toInt(),
        urgent = ((j['counts'] as Json)['urgent'] as num).toInt(),
        late = ((j['counts'] as Json)['late'] as num).toInt(),
        act = (j['act'] as List).cast<Json>().map(TaskItem.new).toList(),
        follow = (j['follow'] as List).cast<Json>().map(TaskItem.new).toList(),
        reasons = (j['reasons'] as List).cast<Json>().map((r) => RejectReason(r['code'] as String, r['label'] as String, r['hint'] as String)).toList();

  final String name;
  final String title;
  final String role;
  final int actTotal;
  final int followTotal;
  final int urgent;
  final int late;
  final List<TaskItem> act;
  final List<TaskItem> follow;
  final List<RejectReason> reasons;

  String get firstName => name.split(' ').first;
}
