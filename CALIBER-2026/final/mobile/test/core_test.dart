import 'package:flutter_test/flutter_test.dart';
import 'package:sparekit_mobile/core/api.dart';
import 'package:sparekit_mobile/core/format.dart';
import 'package:sparekit_mobile/core/lang.dart';
import 'package:sparekit_mobile/core/task.dart';

Json _row(Map<String, Object?> over) => {
      'id': '1001',
      'material_no': 1001,
      'description': 'Seal',
      'unit': 'EA',
      'criticality': 'A',
      'kind': 'order',
      'urgency': 'now',
      'stock': 2,
      'target': 5,
      'qty': 3,
      'order_by': '2026-11-10',
      'days_left': 6,
      'value': 1500000,
      'machines': ['PP-128A'],
      'twin': null,
      'owner': 'Bima Santoso',
      'stage': 'todo',
      'next_to': 'approved',
      'actionable': true,
      'can_reject': true,
      ...over,
    };

void main() {
  setUp(() => Lang.code.value = 'id');

  group('sessionFrom', () {
    test('reads the value out of a full Set-Cookie header', () {
      expect(Api.sessionFrom('sk_session=planner.123.abc; Path=/; HttpOnly; SameSite=Lax; Max-Age=43200; Secure'), 'planner.123.abc');
    });
    test('finds it among other cookies joined by the client', () {
      expect(Api.sessionFrom('other=1; Path=/,sk_session=x.y.z; Path=/'), 'x.y.z');
    });
    test('ignores a cookie that only ends with the same name', () {
      expect(Api.sessionFrom('not_sk_session=x; Path=/'), isNull);
    });
    test('returns null without a header', () => expect(Api.sessionFrom(null), isNull));
  });

  group('format', () {
    test('rupiah follows the language', () {
      expect(rupiah(43100000000), 'Rp 43,1 M');
      Lang.code.value = 'en';
      expect(rupiah(43100000000), 'Rp 43,1 B');
    });
    test('missing values show a dash', () {
      expect(rupiah(null), '–');
      expect(shortDate(null), '–');
    });
    test('whole numbers use a dot for thousands', () => expect(number(12500), '12.500'));
    test('days read correctly on both sides of the deadline', () {
      expect(daysText(-3), 'lewat 3 hari');
      expect(daysText(0), 'hari ini');
      expect(daysText(4), '4 hari lagi');
    });
    test('dates read from the server', () => expect(shortDate('2026-11-10'), '10 Nov 2026'));
  });

  group('TaskItem', () {
    test('an order asks for the amount and approves first', () {
      final t = TaskItem(_row({}));
      expect(t.ask, 'Pesan 3 ea');
      expect(t.nextLabel, 'Setujui');
      expect(t.movedLabel, contains('Bima Santoso'));
    });
    test('the button follows the stage', () {
      expect(TaskItem(_row({'stage': 'approved', 'next_to': 'in_progress'})).nextLabel, 'Mulai');
      expect(TaskItem(_row({'stage': 'in_progress', 'next_to': 'done'})).nextLabel, 'Tandai selesai');
    });
    test('a task still to decide waits for the planner', () {
      expect(TaskItem(_row({'actionable': false})).followLine, 'Menunggu perencana');
      expect(TaskItem(_row({'actionable': false, 'stage': 'approved'})).followLine, contains('Bima Santoso'));
    });
    test('a null value and an empty machine list do not break the card', () {
      final t = TaskItem(_row({'value': null, 'machines': null, 'order_by': null, 'days_left': null}));
      expect(t.value, isNull);
      expect(t.machines, isEmpty);
    });
  });

  test('Inbox reads the whole response', () {
    final inbox = Inbox({
      'me': {'name': 'Nadia Putri', 'title': 'Perencana', 'role': 'planner'},
      'counts': {'act': 1, 'follow': 0, 'urgent': 1, 'late': 0},
      'act': [_row({})],
      'follow': <Json>[],
      'reasons': [
        {'code': 'data', 'label': 'Datanya salah', 'hint': 'Cek rak'},
      ],
    });
    expect(inbox.firstName, 'Nadia');
    expect(inbox.act.single.materialNo, 1001);
    expect(inbox.reasons.single.code, 'data');
  });
}
