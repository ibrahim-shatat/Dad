import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../models/meeting.dart';

class MeetingDetailScreen extends StatelessWidget {
  final Meeting meeting;
  const MeetingDetailScreen({super.key, required this.meeting});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: const Text('Meeting')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          Text(meeting.title,
              style: Theme.of(context)
                  .textTheme
                  .titleLarge
                  ?.copyWith(fontWeight: FontWeight.bold)),
          if (meeting.meetingDate != null) ...[
            const SizedBox(height: 4),
            Text(DateFormat('EEEE, MMM d, yyyy').format(meeting.meetingDate!),
                style: TextStyle(color: scheme.onSurfaceVariant)),
          ],
          const SizedBox(height: 20),
          if (meeting.status == 'failed')
            _banner(
              context,
              'Processing failed. ${meeting.failureReason ?? ''}',
              const Color(0xFFDC2626),
            )
          else if (meeting.summary == null)
            _banner(context, 'Summary is still being generated.', const Color(0xFFD97706)),
          if (meeting.summary != null) ...[
            _sectionTitle(context, 'Summary'),
            const SizedBox(height: 6),
            Text(meeting.summary!, style: const TextStyle(height: 1.4)),
            const SizedBox(height: 22),
          ],
          if (meeting.actionItems.isNotEmpty) ...[
            _sectionTitle(context, 'Action items (${meeting.actionItems.length})'),
            const SizedBox(height: 8),
            ...meeting.actionItems.map((a) => _ActionRow(item: a)),
            const SizedBox(height: 22),
          ],
          if (meeting.decisions.isNotEmpty) ...[
            _sectionTitle(context, 'Decisions (${meeting.decisions.length})'),
            const SizedBox(height: 8),
            ...meeting.decisions.map((d) => _DecisionRow(decision: d)),
          ],
        ],
      ),
    );
  }

  Widget _sectionTitle(BuildContext context, String text) => Text(
        text.toUpperCase(),
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w800,
          letterSpacing: 0.6,
          color: Theme.of(context).colorScheme.primary,
        ),
      );

  Widget _banner(BuildContext context, String text, Color color) => Container(
        margin: const EdgeInsets.only(bottom: 20),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Text(text, style: TextStyle(color: color, fontWeight: FontWeight.w600)),
      );
}

class _ActionRow extends StatelessWidget {
  final ActionItem item;
  const _ActionRow({required this.item});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            item.isDone ? Icons.check_circle : Icons.radio_button_unchecked,
            size: 18,
            color: item.isDone ? const Color(0xFF15864B) : scheme.onSurfaceVariant,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.description,
                  style: TextStyle(
                    height: 1.35,
                    decoration: item.isDone ? TextDecoration.lineThrough : null,
                    color: item.isDone ? scheme.onSurfaceVariant : null,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  [
                    if (item.owner.isNotEmpty) item.owner,
                    if (item.dueDate != null)
                      'due ${DateFormat('MMM d').format(item.dueDate!)}',
                  ].join('  ·  '),
                  style: TextStyle(fontSize: 12, color: scheme.onSurfaceVariant),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _DecisionRow extends StatelessWidget {
  final Decision decision;
  const _DecisionRow({required this.decision});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.gavel_outlined, size: 18, color: scheme.primary),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(decision.description, style: const TextStyle(height: 1.35)),
                const SizedBox(height: 2),
                Text(
                  [
                    if (decision.decidedBy.isNotEmpty) decision.decidedBy,
                    if (decision.deadline != null)
                      'by ${DateFormat('MMM d').format(decision.deadline!)}',
                  ].join('  ·  '),
                  style: TextStyle(fontSize: 12, color: scheme.onSurfaceVariant),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
