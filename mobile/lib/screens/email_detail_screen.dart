import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../api/api_client.dart';
import '../api/email_api.dart';
import '../models/email_message.dart';
import '../state/auth_state.dart';

/// Reads one email in full (body fetched live) with reply / dismiss actions.
/// Pops `true` if something changed (dismissed/restored/drafted) so the list refreshes.
class EmailDetailScreen extends StatefulWidget {
  final EmailMessage message;
  const EmailDetailScreen({super.key, required this.message});

  @override
  State<EmailDetailScreen> createState() => _EmailDetailScreenState();
}

class _EmailDetailScreenState extends State<EmailDetailScreen> {
  final EmailApi _api = EmailApi(ApiClient());
  late Future<EmailBody> _future;
  late bool _hidden = widget.message.isHidden;
  bool _drafted = false;

  @override
  void initState() {
    super.initState();
    final token = context.read<AuthState>().token!;
    _future = _api.messageBody(widget.message.id, token);
  }

  void _toast(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  Future<void> _draftReply() async {
    final token = context.read<AuthState>().token!;
    try {
      await _api.draftReply(widget.message.id, null, token);
      setState(() => _drafted = true);
      _toast('Draft requested — check Approvals.');
    } catch (e) {
      _toast('Could not draft reply: $e');
    }
  }

  Future<void> _toggleHidden() async {
    final token = context.read<AuthState>().token!;
    final wasHidden = _hidden;
    try {
      if (wasHidden) {
        await _api.unhide(widget.message.id, token);
      } else {
        await _api.hide(widget.message.id, token);
      }
      setState(() => _hidden = !wasHidden);
      _toast(wasHidden ? 'Restored to inbox.' : 'Dismissed from inbox.');
    } catch (e) {
      _toast('Could not update: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final m = widget.message;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Message'),
        actions: [
          IconButton(
            tooltip: _hidden ? 'Restore to inbox' : 'Dismiss',
            icon: Icon(_hidden ? Icons.unarchive_outlined : Icons.archive_outlined),
            onPressed: _toggleHidden,
          ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: _drafted
              ? Text('Draft requested — check the Approvals tab.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: scheme.onSurfaceVariant))
              : FilledButton.icon(
                  onPressed: _draftReply,
                  style: FilledButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14)),
                  icon: const Icon(Icons.reply, size: 18),
                  label: const Text('Draft AI reply'),
                ),
        ),
      ),
      body: ListView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
          children: [
            Text(m.subject.isEmpty ? '(no subject)' : m.subject,
                style: Theme.of(context)
                    .textTheme
                    .titleLarge
                    ?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: Text(m.sender,
                      style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 13)),
                ),
                Text(DateFormat('MMM d, h:mm a').format(m.receivedAt.toLocal()),
                    style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12)),
              ],
            ),
            if (m.aiSummary != null && m.aiSummary!.isNotEmpty) ...[
              const SizedBox(height: 14),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: scheme.primary.withOpacity(0.06),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('AI SUMMARY',
                        style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 0.5,
                            color: scheme.primary)),
                    const SizedBox(height: 4),
                    Text(m.aiSummary!, style: const TextStyle(height: 1.4)),
                  ],
                ),
              ),
            ],
            const Divider(height: 28),
            FutureBuilder<EmailBody>(
              future: _future,
              builder: (context, snap) {
                if (snap.connectionState == ConnectionState.waiting) {
                  return const Padding(
                    padding: EdgeInsets.only(top: 24),
                    child: Center(child: CircularProgressIndicator()),
                  );
                }
                if (snap.hasError) {
                  return Text('Could not load the full message.\n${snap.error}',
                      style: TextStyle(color: scheme.onSurfaceVariant));
                }
                final body = snap.data!.body.trim();
                return SelectableText(
                  body.isEmpty ? '(This message has no text body.)' : body,
                  style: const TextStyle(height: 1.5),
                );
              },
            ),
          ],
        ),
      );
  }
}
