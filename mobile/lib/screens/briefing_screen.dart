import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/api_client.dart';
import '../api/briefing_api.dart';
import '../models/briefing.dart';
import '../state/auth_state.dart';

class BriefingScreen extends StatefulWidget {
  const BriefingScreen({super.key});

  @override
  State<BriefingScreen> createState() => _BriefingScreenState();
}

class _BriefingScreenState extends State<BriefingScreen> {
  final BriefingApi _api = BriefingApi(ApiClient());
  late Future<Briefing> _future;
  bool _generating = false;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<Briefing> _load() {
    final token = context.read<AuthState>().token!;
    return _api.today(token);
  }

  Future<void> _refresh() async {
    final next = _load();
    setState(() => _future = next);
    try {
      await next;
    } catch (_) {}
  }

  Future<void> _generate() async {
    final token = context.read<AuthState>().token!;
    setState(() => _generating = true);
    try {
      final b = await _api.generate(token);
      if (!mounted) return;
      setState(() => _future = Future.value(b));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Could not generate: $e')));
    } finally {
      if (mounted) setState(() => _generating = false);
    }
  }

  Future<void> _toggle(BriefingItem item) async {
    final token = context.read<AuthState>().token!;
    try {
      final b = await _api.toggle(item.key, !item.handled, token);
      if (!mounted) return;
      setState(() => _future = Future.value(b));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Could not update: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Daily briefing'),
        actions: [
          IconButton(
            icon: _generating
                ? const SizedBox(
                    height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.refresh),
            tooltip: 'Regenerate',
            onPressed: _generating ? null : _generate,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<Briefing>(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState == ConnectionState.waiting) {
              return ListView(children: const [
                SizedBox(height: 120),
                Center(child: CircularProgressIndicator()),
              ]);
            }
            if (snap.hasError) {
              return _centered(context, 'Could not load briefing.\n${snap.error}');
            }
            final b = snap.data!;
            return ListView(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
              children: [
                if (b.totalItems > 0)
                  Text('${b.handledItems} of ${b.totalItems} handled',
                      style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12.5)),
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: scheme.primary.withOpacity(0.06),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: scheme.primary.withOpacity(0.18)),
                  ),
                  child: b.summary != null && b.summary!.isNotEmpty
                      ? Text(b.summary!, style: const TextStyle(height: 1.45))
                      : Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('No summary yet for today.',
                                style: TextStyle(color: scheme.onSurfaceVariant)),
                            const SizedBox(height: 10),
                            FilledButton.icon(
                              onPressed: _generating ? null : _generate,
                              icon: const Icon(Icons.auto_awesome, size: 18),
                              label: const Text('Generate briefing'),
                            ),
                          ],
                        ),
                ),
                if (b.topPriorities.isNotEmpty) ...[
                  const SizedBox(height: 20),
                  _title(context, 'Top priorities'),
                  const SizedBox(height: 8),
                  ...b.topPriorities.map((p) => Padding(
                        padding: const EdgeInsets.only(bottom: 6),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('•  ', style: TextStyle(color: scheme.primary)),
                            Expanded(child: Text(p, style: const TextStyle(height: 1.35))),
                          ],
                        ),
                      )),
                ],
                for (final section in b.sections)
                  if (section.items.isNotEmpty) ...[
                    const SizedBox(height: 20),
                    _title(context, '${section.label} (${section.items.length})'),
                    const SizedBox(height: 6),
                    ...section.items.map((it) => _ItemTile(item: it, onToggle: () => _toggle(it))),
                  ],
              ],
            );
          },
        ),
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

class _ItemTile extends StatelessWidget {
  final BriefingItem item;
  final VoidCallback onToggle;
  const _ItemTile({required this.item, required this.onToggle});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return InkWell(
      onTap: onToggle,
      borderRadius: BorderRadius.circular(10),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(
              item.handled ? Icons.check_circle : Icons.radio_button_unchecked,
              size: 20,
              color: item.handled ? const Color(0xFF15864B) : scheme.onSurfaceVariant,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.title,
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      decoration: item.handled ? TextDecoration.lineThrough : null,
                      color: item.handled ? scheme.onSurfaceVariant : null,
                    ),
                  ),
                  if (item.subtitle != null && item.subtitle!.isNotEmpty) ...[
                    const SizedBox(height: 2),
                    Text(item.subtitle!,
                        style: TextStyle(fontSize: 12.5, color: scheme.onSurfaceVariant)),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
