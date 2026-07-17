import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../api/api_client.dart';
import '../api/email_api.dart';
import '../models/email_account.dart';
import '../models/email_message.dart';
import '../state/auth_state.dart';

class _Inbox {
  final Map<String, EmailAccount> accountsById;
  final List<EmailMessage> messages;
  _Inbox(this.accountsById, this.messages);
}

class EmailScreen extends StatefulWidget {
  const EmailScreen({super.key});

  @override
  State<EmailScreen> createState() => _EmailScreenState();
}

class _EmailScreenState extends State<EmailScreen> {
  final EmailApi _api = EmailApi(ApiClient());
  late Future<_Inbox> _future;
  final Set<String> _queued = {};

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<_Inbox> _load() async {
    final token = context.read<AuthState>().token!;
    final accounts = await _api.accounts(token);
    final messages = await _api.messages(token);
    return _Inbox({for (final a in accounts) a.id: a}, messages);
  }

  Future<void> _refresh() async {
    final next = _load();
    setState(() => _future = next);
    try {
      await next;
    } catch (_) {}
  }

  Future<void> _draftReply(EmailMessage m) async {
    final token = context.read<AuthState>().token!;
    try {
      await _api.draftReply(m.id, null, token);
      if (!mounted) return;
      setState(() => _queued.add(m.id));
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Draft requested — check Approvals shortly.')),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Could not draft reply: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Email')),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<_Inbox>(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState == ConnectionState.waiting) {
              return ListView(children: const [
                SizedBox(height: 120),
                Center(child: CircularProgressIndicator()),
              ]);
            }
            if (snap.hasError) {
              return _Message(text: 'Could not load email.\n${snap.error}');
            }
            final inbox = snap.data!;
            if (inbox.accountsById.isEmpty) {
              return _Message(
                text:
                    'No mailbox connected yet.\nConnect Gmail from the web console, then pull to refresh.',
              );
            }
            if (inbox.messages.isEmpty) {
              return _Message(text: 'No messages synced yet.\nPull down to refresh.');
            }
            return ListView.builder(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 24),
              itemCount: inbox.messages.length,
              itemBuilder: (context, i) {
                final m = inbox.messages[i];
                return _MessageCard(
                  message: m,
                  provider: inbox.accountsById[m.accountId]?.provider,
                  queued: _queued.contains(m.id),
                  onDraftReply: () => _draftReply(m),
                );
              },
            );
          },
        ),
      ),
    );
  }
}

Color _urgencyColor(String? urgency) {
  switch (urgency) {
    case 'high':
      return const Color(0xFFDC2626);
    case 'medium':
      return const Color(0xFFD97706);
    default:
      return const Color(0xFF6B7280);
  }
}

class _MessageCard extends StatelessWidget {
  final EmailMessage message;
  final String? provider;
  final bool queued;
  final VoidCallback onDraftReply;

  const _MessageCard({
    required this.message,
    required this.provider,
    required this.queued,
    required this.onDraftReply,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final high = message.aiUrgency == 'high';
    final providerColor =
        provider == 'outlook' ? const Color(0xFF2563EB) : const Color(0xFFDC2626);
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: scheme.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: high
              ? const Color(0xFFDC2626).withOpacity(0.35)
              : scheme.outlineVariant.withOpacity(0.5),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              if (provider != null) _pill(provider!.toUpperCase(), providerColor),
              if (message.aiUrgency != null) ...[
                const SizedBox(width: 6),
                _pill('${message.aiUrgency!.toUpperCase()} URGENCY',
                    _urgencyColor(message.aiUrgency)),
              ],
              const Spacer(),
              Text(
                DateFormat('MMM d, h:mm a').format(message.receivedAt.toLocal()),
                style: TextStyle(fontSize: 11, color: scheme.onSurfaceVariant),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(message.sender,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontWeight: FontWeight.w700)),
          Text(message.subject,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 4),
          Text(
            message.aiSummary ?? message.snippet,
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(fontSize: 13, color: scheme.onSurfaceVariant),
          ),
          const SizedBox(height: 10),
          Align(
            alignment: Alignment.centerLeft,
            child: queued
                ? Text('Draft requested ✓',
                    style: TextStyle(fontSize: 12.5, color: scheme.onSurfaceVariant))
                : OutlinedButton.icon(
                    onPressed: onDraftReply,
                    icon: const Icon(Icons.reply, size: 16),
                    label: const Text('Draft reply'),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _pill(String text, Color color) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
        decoration: BoxDecoration(
          color: color.withOpacity(0.12),
          borderRadius: BorderRadius.circular(99),
        ),
        child: Text(text,
            style: TextStyle(
                fontSize: 9, fontWeight: FontWeight.w800, color: color, letterSpacing: 0.3)),
      );
}

class _Message extends StatelessWidget {
  final String text;
  const _Message({required this.text});

  @override
  Widget build(BuildContext context) {
    return ListView(
      children: [
        const SizedBox(height: 120),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32),
          child: Text(
            text,
            textAlign: TextAlign.center,
            style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
          ),
        ),
      ],
    );
  }
}
