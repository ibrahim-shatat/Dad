import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/api_client.dart';
import '../api/dashboard_api.dart';
import '../api/meetings_api.dart';
import '../models/attention_item.dart';
import '../models/dashboard_summary.dart';
import '../state/auth_state.dart';
import '../state/nav_state.dart';
import '../widgets/attention_row.dart';
import 'documents_screen.dart';
import 'meeting_detail_screen.dart';

/// "Prepare My Day" — the app's home. Shows the priority-ranked attention feed
/// plus the key counters, pulled live from GET /dashboard.
class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final DashboardApi _api = DashboardApi(ApiClient());
  late Future<DashboardSummary> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<DashboardSummary> _load() {
    final token = context.read<AuthState>().token!;
    return _api.fetch(token);
  }

  Future<void> _refresh() async {
    final next = _load();
    setState(() => _future = next);
    // Await so the pull-to-refresh spinner stays until the request settles;
    // swallow errors here since the FutureBuilder renders the error state.
    try {
      await next;
    } catch (_) {}
  }

  String _greeting() {
    final h = DateTime.now().hour;
    if (h < 12) return 'Good morning';
    if (h < 18) return 'Good afternoon';
    return 'Good evening';
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthState>();
    final fullName = (auth.user?.fullName ?? '').trim();
    final firstName = fullName.isEmpty ? '' : fullName.split(' ').first;
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Prepare My Day'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Log out',
            onPressed: () => auth.logout(),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<DashboardSummary>(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState == ConnectionState.waiting) {
              return ListView(
                children: const [
                  SizedBox(height: 120),
                  Center(child: CircularProgressIndicator()),
                ],
              );
            }
            if (snap.hasError) {
              return _ErrorView(message: snap.error.toString(), onRetry: _refresh);
            }
            final data = snap.data!;
            return ListView(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
              children: [
                Text(
                  '${_greeting()}${firstName.isNotEmpty ? ', $firstName' : ''}.',
                  style: Theme.of(context)
                      .textTheme
                      .headlineSmall
                      ?.copyWith(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                Text(
                  "Here's what needs you today.",
                  style: TextStyle(color: scheme.onSurfaceVariant),
                ),
                const SizedBox(height: 20),
                _AttentionCard(items: data.needsAttention),
                if (data.needsWork.isNotEmpty) ...[
                  const SizedBox(height: 20),
                  _WorkCard(items: data.needsWork),
                ],
                const SizedBox(height: 20),
                _StatGrid(data: data),
              ],
            );
          },
        ),
      ),
    );
  }
}

/// Routes a tapped attention/work item to the right place. Items whose link points at a
/// specific meeting open that meeting directly; others switch to the relevant tab.
Future<void> openAttentionItem(BuildContext context, AttentionItem item) async {
  final link = item.link;
  if (link.startsWith('/meetings/')) {
    final id = link.substring('/meetings/'.length);
    final token = context.read<AuthState>().token!;
    try {
      final meeting = await MeetingsApi(ApiClient()).get(id, token);
      if (context.mounted) {
        Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => MeetingDetailScreen(meeting: meeting)),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Could not open meeting: $e')));
      }
    }
    return;
  }
  switch (item.kind) {
    case 'email':
      context.read<NavState>().go(NavState.email);
      break;
    case 'approval':
      context.read<NavState>().go(NavState.approvals);
      break;
    case 'event':
      context.read<NavState>().go(NavState.calendar);
      break;
    case 'document':
      Navigator.of(context)
          .push(MaterialPageRoute(builder: (_) => const DocumentsScreen()));
      break;
  }
}

class _AttentionCard extends StatelessWidget {
  final List<AttentionItem> items;
  const _AttentionCard({required this.items});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: scheme.primary.withOpacity(0.06),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: scheme.primary.withOpacity(0.18)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.auto_awesome, size: 18, color: scheme.primary),
              const SizedBox(width: 8),
              Text(
                'What needs your attention',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 15,
                  color: scheme.primary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          if (items.isEmpty)
            Text(
              "You're all caught up. Nothing is pressing right now.",
              style: TextStyle(color: scheme.onSurfaceVariant),
            )
          else ...[
            Text(
              '${items.length} thing${items.length > 1 ? 's' : ''} may need you today — ranked by urgency.',
              style: TextStyle(color: scheme.onSurface, fontSize: 13),
            ),
            const SizedBox(height: 12),
            ...items.map((i) => AttentionRow(item: i, onTap: () => openAttentionItem(context, i))),
          ],
        ],
      ),
    );
  }
}

class _WorkCard extends StatelessWidget {
  final List<AttentionItem> items;
  const _WorkCard({required this.items});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: scheme.surface,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: scheme.outlineVariant.withOpacity(0.5)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.checklist_rounded, size: 18, color: scheme.primary),
              const SizedBox(width: 8),
              Text('What needs work',
                  style: TextStyle(
                      fontWeight: FontWeight.bold, fontSize: 15, color: scheme.onSurface)),
            ],
          ),
          const SizedBox(height: 4),
          Text('Tasks, documents, and presentations in progress.',
              style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12.5)),
          const SizedBox(height: 12),
          ...items.map((i) => AttentionRow(item: i, onTap: () => openAttentionItem(context, i))),
        ],
      ),
    );
  }
}

class _StatGrid extends StatelessWidget {
  final DashboardSummary data;
  const _StatGrid({required this.data});

  @override
  Widget build(BuildContext context) {
    final tiles = <Widget>[
      _Stat('Urgent emails', data.unreadUrgentEmails, Icons.mail_outline,
          urgent: data.unreadUrgentEmails > 0),
      _Stat('Pending approvals', data.pendingApprovals, Icons.verified_outlined),
      _Stat('Open action items', data.openActionItems, Icons.checklist_outlined),
      _Stat('Docs to review', data.documentsAwaitingReview, Icons.description_outlined),
    ];
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 10,
      crossAxisSpacing: 10,
      childAspectRatio: 1.9,
      children: tiles,
    );
  }
}

class _Stat extends StatelessWidget {
  final String label;
  final int value;
  final IconData icon;
  final bool urgent;
  const _Stat(this.label, this.value, this.icon, {this.urgent = false});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final accent = urgent ? const Color(0xFFDC2626) : scheme.primary;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: scheme.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: scheme.outlineVariant.withOpacity(0.5)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Icon(icon, size: 18, color: accent),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '$value',
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                  color: urgent ? accent : null,
                ),
              ),
              Text(
                label,
                style: TextStyle(fontSize: 11.5, color: scheme.onSurfaceVariant),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String message;
  final Future<void> Function() onRetry;
  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return ListView(
      padding: const EdgeInsets.symmetric(horizontal: 32),
      children: [
        const SizedBox(height: 100),
        Icon(Icons.cloud_off_outlined, size: 40, color: scheme.onSurfaceVariant),
        const SizedBox(height: 12),
        Text(
          message,
          textAlign: TextAlign.center,
          style: TextStyle(color: scheme.onSurfaceVariant),
        ),
        const SizedBox(height: 8),
        Text(
          'Pull down to try again.',
          textAlign: TextAlign.center,
          style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12),
        ),
        const SizedBox(height: 16),
        Center(
          child: OutlinedButton(onPressed: onRetry, child: const Text('Retry')),
        ),
      ],
    );
  }
}
