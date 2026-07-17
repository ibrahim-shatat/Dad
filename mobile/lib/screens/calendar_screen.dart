import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../api/api_client.dart';
import '../api/calendar_api.dart';
import '../models/calendar_event.dart';
import '../state/auth_state.dart';

class CalendarScreen extends StatefulWidget {
  const CalendarScreen({super.key});

  @override
  State<CalendarScreen> createState() => _CalendarScreenState();
}

class _CalendarScreenState extends State<CalendarScreen> {
  final CalendarApi _api = CalendarApi(ApiClient());
  late Future<List<CalendarEvent>> _future;
  final Set<String> _prepRequested = {};

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<List<CalendarEvent>> _load() {
    final token = context.read<AuthState>().token!;
    return _api.events(token);
  }

  Future<void> _refresh() async {
    final next = _load();
    setState(() => _future = next);
    try {
      await next;
    } catch (_) {}
  }

  Future<void> _generatePrep(CalendarEvent e) async {
    final token = context.read<AuthState>().token!;
    try {
      await _api.generatePrep(e.id, token);
      if (!mounted) return;
      setState(() => _prepRequested.add(e.id));
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Preparing brief — pull to refresh in a moment.')),
      );
    } catch (err) {
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Could not prepare brief: $err')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Calendar')),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<CalendarEvent>>(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState == ConnectionState.waiting) {
              return ListView(children: const [
                SizedBox(height: 120),
                Center(child: CircularProgressIndicator()),
              ]);
            }
            if (snap.hasError) {
              return _centered(context, 'Could not load calendar.\n${snap.error}');
            }
            final events = snap.data!;
            if (events.isEmpty) {
              return _centered(context,
                  'No upcoming events.\nConnect Gmail (with calendar) from the web console.');
            }
            return ListView.builder(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 24),
              itemCount: events.length,
              itemBuilder: (context, i) => _EventCard(
                event: events[i],
                prepRequested: _prepRequested.contains(events[i].id),
                onGeneratePrep: () => _generatePrep(events[i]),
                showDayHeader: i == 0 ||
                    !_sameDay(events[i - 1].startTime, events[i].startTime),
              ),
            );
          },
        ),
      ),
    );
  }

  bool _sameDay(DateTime a, DateTime b) {
    final la = a.toLocal(), lb = b.toLocal();
    return la.year == lb.year && la.month == lb.month && la.day == lb.day;
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

class _EventCard extends StatelessWidget {
  final CalendarEvent event;
  final bool prepRequested;
  final bool showDayHeader;
  final VoidCallback onGeneratePrep;

  const _EventCard({
    required this.event,
    required this.prepRequested,
    required this.showDayHeader,
    required this.onGeneratePrep,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final start = event.startTime.toLocal();
    final timeLabel = event.isAllDay
        ? 'All day'
        : DateFormat('h:mm a').format(start) +
            (event.endTime != null
                ? ' – ${DateFormat('h:mm a').format(event.endTime!.toLocal())}'
                : '');

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (showDayHeader)
          Padding(
            padding: const EdgeInsets.fromLTRB(4, 10, 4, 8),
            child: Text(
              DateFormat('EEEE, MMM d').format(start),
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w800,
                letterSpacing: 0.5,
                color: scheme.primary,
              ),
            ),
          ),
        Container(
          margin: const EdgeInsets.only(bottom: 10),
          decoration: BoxDecoration(
            color: scheme.surface,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: scheme.outlineVariant.withOpacity(0.5)),
          ),
          child: Theme(
            data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
            child: ExpansionTile(
              tilePadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 2),
              childrenPadding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
              title: Text(event.title,
                  style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
              subtitle: Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(
                  [
                    timeLabel,
                    if (event.location != null && event.location!.isNotEmpty) event.location!,
                    if (event.attendees.isNotEmpty) '${event.attendees.length} attendees',
                  ].join('  ·  '),
                  style: TextStyle(fontSize: 12.5, color: scheme.onSurfaceVariant),
                ),
              ),
              children: [
                if (event.description != null && event.description!.isNotEmpty) ...[
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Text(event.description!, style: const TextStyle(height: 1.4)),
                  ),
                  const SizedBox(height: 12),
                ],
                if (event.prepBrief != null && event.prepBrief!.isNotEmpty)
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: scheme.primary.withOpacity(0.06),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('PREP BRIEF',
                            style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w800,
                                letterSpacing: 0.5,
                                color: scheme.primary)),
                        const SizedBox(height: 6),
                        Text(event.prepBrief!, style: const TextStyle(height: 1.4)),
                      ],
                    ),
                  )
                else
                  Align(
                    alignment: Alignment.centerLeft,
                    child: prepRequested
                        ? Text('Preparing brief…',
                            style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12.5))
                        : OutlinedButton.icon(
                            onPressed: onGeneratePrep,
                            icon: const Icon(Icons.auto_awesome, size: 16),
                            label: const Text('Generate prep brief'),
                          ),
                  ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
