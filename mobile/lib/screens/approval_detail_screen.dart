import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/api_client.dart';
import '../api/approvals_api.dart';
import '../api/email_api.dart';
import '../models/approval_item.dart';
import '../models/email_draft.dart';
import '../state/auth_state.dart';

/// Full review of an approval item before actioning it. For email drafts it loads
/// and shows the complete message (to / cc / subject / body). Pops `true` if the
/// item was approved or rejected so the list can refresh.
class ApprovalDetailScreen extends StatefulWidget {
  final ApprovalItem item;
  const ApprovalDetailScreen({super.key, required this.item});

  @override
  State<ApprovalDetailScreen> createState() => _ApprovalDetailScreenState();
}

class _ApprovalDetailScreenState extends State<ApprovalDetailScreen> {
  final ApiClient _client = ApiClient();
  late final ApprovalsApi _approvals = ApprovalsApi(_client);
  late final EmailApi _email = EmailApi(_client);

  Future<EmailDraft>? _draftFuture;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    if (widget.item.isEmailDraft) {
      final token = context.read<AuthState>().token!;
      _draftFuture = _email.draft(widget.item.referenceId, token);
    }
  }

  void _toast(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  Future<void> _approve() async {
    final token = context.read<AuthState>().token!;
    setState(() => _busy = true);
    try {
      await _approvals.approve(widget.item.id, token);
      if (!mounted) return;
      Navigator.of(context).pop(true);
    } catch (e) {
      setState(() => _busy = false);
      _toast('Could not approve: $e');
    }
  }

  Future<void> _reject() async {
    final reason = await _askReason();
    if (reason == null || reason.trim().isEmpty) return;
    final token = context.read<AuthState>().token!;
    setState(() => _busy = true);
    try {
      await _approvals.reject(widget.item.id, reason.trim(), token);
      if (!mounted) return;
      Navigator.of(context).pop(true);
    } catch (e) {
      setState(() => _busy = false);
      _toast('Could not reject: $e');
    }
  }

  Future<String?> _askReason() {
    final controller = TextEditingController();
    return showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Reason for rejecting'),
        content: TextField(
          controller: controller,
          autofocus: true,
          maxLines: 3,
          decoration: const InputDecoration(
            hintText: 'Why is this being rejected?',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(
            onPressed: () => Navigator.pop(context, controller.text),
            child: const Text('Reject'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: Text(widget.item.typeLabel)),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: _busy
              ? const Center(
                  child: Padding(
                    padding: EdgeInsets.all(8),
                    child: SizedBox(
                        height: 22, width: 22, child: CircularProgressIndicator(strokeWidth: 2)),
                  ),
                )
              : Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: _reject,
                        style: OutlinedButton.styleFrom(
                          foregroundColor: const Color(0xFFDC2626),
                          side: const BorderSide(color: Color(0x55DC2626)),
                          padding: const EdgeInsets.symmetric(vertical: 14),
                        ),
                        icon: const Icon(Icons.close, size: 18),
                        label: const Text('Reject'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: FilledButton.icon(
                        onPressed: _approve,
                        style: FilledButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 14),
                        ),
                        icon: const Icon(Icons.check, size: 18),
                        label: const Text('Approve'),
                      ),
                    ),
                  ],
                ),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
        children: [
          if (widget.item.requestedByName != null)
            Text('Requested by ${widget.item.requestedByName}',
                style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12.5)),
          const SizedBox(height: 12),
          if (widget.item.isEmailDraft)
            FutureBuilder<EmailDraft>(
              future: _draftFuture,
              builder: (context, snap) {
                if (snap.connectionState == ConnectionState.waiting) {
                  return const Padding(
                    padding: EdgeInsets.only(top: 40),
                    child: Center(child: CircularProgressIndicator()),
                  );
                }
                if (snap.hasError) {
                  return _fallbackPreview(
                      context, 'Could not load the full draft.\n${snap.error}');
                }
                return _DraftView(draft: snap.data!);
              },
            )
          else
            _fallbackPreview(context, widget.item.previewText),
        ],
      ),
    );
  }

  Widget _fallbackPreview(BuildContext context, String text) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: scheme.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: scheme.outlineVariant.withOpacity(0.5)),
      ),
      child: Text(text, style: const TextStyle(height: 1.4)),
    );
  }
}

class _DraftView extends StatelessWidget {
  final EmailDraft draft;
  const _DraftView({required this.draft});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: scheme.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: scheme.outlineVariant.withOpacity(0.5)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _field(context, 'To', draft.toAddresses.join(', ')),
          if (draft.ccAddresses.isNotEmpty)
            _field(context, 'Cc', draft.ccAddresses.join(', ')),
          _field(context, 'Subject', draft.subject.isEmpty ? '(no subject)' : draft.subject),
          const Divider(height: 24),
          Text(draft.body, style: const TextStyle(height: 1.5)),
        ],
      ),
    );
  }

  Widget _field(BuildContext context, String label, String value) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: RichText(
        text: TextSpan(
          style: DefaultTextStyle.of(context).style,
          children: [
            TextSpan(
              text: '$label:  ',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w800,
                letterSpacing: 0.3,
                color: scheme.onSurfaceVariant,
              ),
            ),
            TextSpan(text: value, style: const TextStyle(fontWeight: FontWeight.w500)),
          ],
        ),
      ),
    );
  }
}
