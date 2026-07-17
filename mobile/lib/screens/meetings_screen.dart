import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../api/api_client.dart';
import '../api/meetings_api.dart';
import '../models/meeting.dart';
import '../state/auth_state.dart';
import 'meeting_detail_screen.dart';
import 'new_meeting_screen.dart';

class MeetingsScreen extends StatefulWidget {
  const MeetingsScreen({super.key});

  @override
  State<MeetingsScreen> createState() => _MeetingsScreenState();
}

class _MeetingsScreenState extends State<MeetingsScreen> {
  final MeetingsApi _api = MeetingsApi(ApiClient());
  late Future<List<Meeting>> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<List<Meeting>> _load() {
    final token = context.read<AuthState>().token!;
    return _api.list(token);
  }

  Future<void> _refresh() async {
    final next = _load();
    setState(() => _future = next);
    try {
      await next;
    } catch (_) {}
  }

  Future<void> _openNew() async {
    final created = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => const NewMeetingScreen()),
    );
    if (created == true) {
      await _refresh();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Meeting created — analyzing. Pull to refresh shortly.')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Meetings')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _openNew,
        icon: const Icon(Icons.add),
        label: const Text('New'),
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<Meeting>>(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState == ConnectionState.waiting) {
              return ListView(children: const [
                SizedBox(height: 120),
                Center(child: CircularProgressIndicator()),
              ]);
            }
            if (snap.hasError) {
              return _centered(context, 'Could not load meetings.\n${snap.error}');
            }
            final meetings = snap.data!;
            if (meetings.isEmpty) {
              return _centered(
                  context, 'No meetings yet.\nAdd meeting notes from the web console.');
            }
            return ListView.builder(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 24),
              itemCount: meetings.length,
              itemBuilder: (context, i) => _MeetingCard(meeting: meetings[i]),
            );
          },
        ),
      ),
    );
  }

  Widget _centered(BuildContext context, String text) => ListView(
        children: [
          const SizedBox(height: 120),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 32),
            child: Text(text,
                textAlign: TextAlign.center,
                style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant)),
          ),
        ],
      );
}

/// Meeting processing states → a colored chip.
Color meetingStatusColor(String status) {
  switch (status) {
    case 'completed':
    case 'processed':
      return const Color(0xFF15864B);
    case 'failed':
      return const Color(0xFFDC2626);
    case 'processing':
    case 'pending':
      return const Color(0xFFD97706);
    default:
      return const Color(0xFF6B7280);
  }
}

class _MeetingCard extends StatelessWidget {
  final Meeting meeting;
  const _MeetingCard({required this.meeting});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final openActions = meeting.actionItems.where((a) => !a.isDone).length;
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: scheme.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: scheme.outlineVariant.withOpacity(0.5)),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => MeetingDetailScreen(meeting: meeting)),
        ),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(meeting.title,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
                  ),
                  const SizedBox(width: 8),
                  _chip(meeting.status, meetingStatusColor(meeting.status)),
                ],
              ),
              const SizedBox(height: 6),
              Text(
                [
                  if (meeting.meetingDate != null)
                    DateFormat('MMM d, yyyy').format(meeting.meetingDate!),
                  '$openActions open action${openActions == 1 ? '' : 's'}',
                  '${meeting.decisions.length} decision${meeting.decisions.length == 1 ? '' : 's'}',
                ].join('  ·  '),
                style: TextStyle(fontSize: 12.5, color: scheme.onSurfaceVariant),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _chip(String text, Color color) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(
          color: color.withOpacity(0.12),
          borderRadius: BorderRadius.circular(99),
        ),
        child: Text(text.toUpperCase(),
            style: TextStyle(
                fontSize: 9.5, fontWeight: FontWeight.w800, color: color, letterSpacing: 0.4)),
      );
}
