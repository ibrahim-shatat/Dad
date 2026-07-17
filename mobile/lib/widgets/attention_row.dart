import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../models/attention_item.dart';

/// A single row in the "What needs your attention" feed — tone-colored icon,
/// title/subtitle, a badge chip, and a relative time.
class AttentionRow extends StatelessWidget {
  final AttentionItem item;
  const AttentionRow({super.key, required this.item});

  Color _tone(BuildContext context) {
    switch (item.tone) {
      case 'urgent':
        return const Color(0xFFDC2626);
      case 'warning':
        return const Color(0xFFD97706);
      default:
        return Theme.of(context).colorScheme.primary;
    }
  }

  IconData _icon() {
    switch (item.kind) {
      case 'email':
        return Icons.mail_outline;
      case 'approval':
        return Icons.send_outlined;
      case 'deadline':
        return Icons.checklist_outlined;
      case 'event':
        return Icons.event_outlined;
      default:
        return Icons.auto_awesome_outlined;
    }
  }

  String? _whenLabel() {
    if (item.when == null) return null;
    final d = item.when!.toLocal();
    final now = DateTime.now();
    final sameDay = d.year == now.year && d.month == now.month && d.day == now.day;
    return sameDay ? DateFormat('h:mm a').format(d) : DateFormat('MMM d').format(d);
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tone = _tone(context);
    final when = _whenLabel();
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: scheme.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: scheme.outlineVariant.withOpacity(0.5)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(
              color: tone.withOpacity(0.12),
              borderRadius: BorderRadius.circular(9),
            ),
            child: Icon(_icon(), size: 18, color: tone),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.title,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 2),
                Text(
                  item.subtitle,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontSize: 12.5, color: scheme.onSurfaceVariant),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: tone.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(99),
                ),
                child: Text(
                  item.badge.toUpperCase(),
                  style: TextStyle(
                    fontSize: 9.5,
                    fontWeight: FontWeight.w800,
                    color: tone,
                    letterSpacing: 0.4,
                  ),
                ),
              ),
              if (when != null) ...[
                const SizedBox(height: 4),
                Text(
                  when,
                  style: TextStyle(fontSize: 10, color: scheme.onSurfaceVariant),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }
}
