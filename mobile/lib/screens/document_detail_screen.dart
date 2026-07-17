import 'package:flutter/material.dart';

import '../models/document.dart';

class DocumentDetailScreen extends StatelessWidget {
  final Document doc;
  const DocumentDetailScreen({super.key, required this.doc});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final review = doc.review;
    return Scaffold(
      appBar: AppBar(title: const Text('Document')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          Text(doc.filename,
              style: Theme.of(context)
                  .textTheme
                  .titleLarge
                  ?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text('${doc.sizeLabel}  ·  ${doc.status}',
              style: TextStyle(color: scheme.onSurfaceVariant)),
          const SizedBox(height: 20),
          if (review == null)
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: (doc.status == 'failed'
                        ? const Color(0xFFDC2626)
                        : const Color(0xFFD97706))
                    .withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                doc.status == 'failed'
                    ? 'Review failed. ${doc.failureReason ?? ''}'
                    : 'The AI review is still being prepared. Pull to refresh on the list.',
                style: TextStyle(
                  color: doc.status == 'failed'
                      ? const Color(0xFFDC2626)
                      : const Color(0xFFB45309),
                  fontWeight: FontWeight.w600,
                ),
              ),
            )
          else ...[
            _title(context, 'Executive summary'),
            const SizedBox(height: 6),
            Text(review.executiveSummary, style: const TextStyle(height: 1.45)),
            const SizedBox(height: 22),
            if (review.riskFlags.isNotEmpty) ...[
              _title(context, 'Risks & issues (${review.riskFlags.length})'),
              const SizedBox(height: 8),
              ...review.riskFlags.map((r) => _RiskCard(flag: r)),
              const SizedBox(height: 22),
            ],
            _title(context, 'Suggested rewrite'),
            const SizedBox(height: 6),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: scheme.primary.withOpacity(0.06),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(review.suggestedRewrite, style: const TextStyle(height: 1.45)),
            ),
            const SizedBox(height: 16),
            Text('Reviewed by ${review.modelUsed}',
                style: TextStyle(fontSize: 11, color: scheme.onSurfaceVariant)),
          ],
        ],
      ),
    );
  }

  Widget _title(BuildContext context, String text) => Text(
        text.toUpperCase(),
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w800,
          letterSpacing: 0.6,
          color: Theme.of(context).colorScheme.primary,
        ),
      );
}

Color _severityColor(String severity) {
  switch (severity) {
    case 'high':
      return const Color(0xFFDC2626);
    case 'medium':
      return const Color(0xFFD97706);
    default:
      return const Color(0xFF6B7280);
  }
}

class _RiskCard extends StatelessWidget {
  final RiskFlag flag;
  const _RiskCard({required this.flag});

  @override
  Widget build(BuildContext context) {
    final color = _severityColor(flag.severity);
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border(left: BorderSide(color: color, width: 3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(flag.category,
                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(99),
                ),
                child: Text(flag.severity.toUpperCase(),
                    style: TextStyle(
                        fontSize: 9, fontWeight: FontWeight.w800, color: color, letterSpacing: 0.3)),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(flag.description,
              style: TextStyle(
                  fontSize: 13,
                  height: 1.35,
                  color: Theme.of(context).colorScheme.onSurfaceVariant)),
        ],
      ),
    );
  }
}
