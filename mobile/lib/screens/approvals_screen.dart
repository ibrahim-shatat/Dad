import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../api/api_client.dart';
import '../api/approvals_api.dart';
import '../models/approval_item.dart';
import '../state/auth_state.dart';
import 'approval_detail_screen.dart';

class ApprovalsScreen extends StatefulWidget {
  const ApprovalsScreen({super.key});

  @override
  State<ApprovalsScreen> createState() => _ApprovalsScreenState();
}

class _ApprovalsScreenState extends State<ApprovalsScreen> {
  final ApprovalsApi _api = ApprovalsApi(ApiClient());
  late Future<List<ApprovalItem>> _future;
  final Set<String> _busy = {};

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<List<ApprovalItem>> _load() {
    final token = context.read<AuthState>().token!;
    return _api.pending(token);
  }

  Future<void> _refresh() async {
    final next = _load();
    setState(() => _future = next);
    try {
      await next;
    } catch (_) {}
  }

  void _toast(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  Future<void> _approve(ApprovalItem item) async {
    final token = context.read<AuthState>().token!;
    setState(() => _busy.add(item.id));
    try {
      await _api.approve(item.id, token);
      _toast('Approved.');
      await _refresh();
    } catch (e) {
      _toast('Could not approve: $e');
    } finally {
      if (mounted) setState(() => _busy.remove(item.id));
    }
  }

  Future<void> _reject(ApprovalItem item) async {
    final reason = await _askReason();
    if (reason == null || reason.trim().isEmpty) return;
    final token = context.read<AuthState>().token!;
    setState(() => _busy.add(item.id));
    try {
      await _api.reject(item.id, reason.trim(), token);
      _toast('Rejected.');
      await _refresh();
    } catch (e) {
      _toast('Could not reject: $e');
    } finally {
      if (mounted) setState(() => _busy.remove(item.id));
    }
  }

  Future<void> _openDetail(ApprovalItem item) async {
    final actioned = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => ApprovalDetailScreen(item: item)),
    );
    if (actioned == true) await _refresh();
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
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
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
    return Scaffold(
      appBar: AppBar(title: const Text('Approvals')),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<ApprovalItem>>(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState == ConnectionState.waiting) {
              return ListView(children: const [
                SizedBox(height: 120),
                Center(child: CircularProgressIndicator()),
              ]);
            }
            if (snap.hasError) {
              return _centered(context, 'Could not load approvals.\n${snap.error}');
            }
            final items = snap.data!;
            if (items.isEmpty) {
              return _centered(context, 'Nothing waiting for approval. 🎉');
            }
            return ListView.builder(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 24),
              itemCount: items.length,
              itemBuilder: (context, i) => _ApprovalCard(
                item: items[i],
                busy: _busy.contains(items[i].id),
                onApprove: () => _approve(items[i]),
                onReject: () => _reject(items[i]),
                onOpen: items[i].isEmailDraft ? () => _openDetail(items[i]) : null,
              ),
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
            child: Text(
              text,
              textAlign: TextAlign.center,
              style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
            ),
          ),
        ],
      );
}

class _ApprovalCard extends StatelessWidget {
  final ApprovalItem item;
  final bool busy;
  final VoidCallback onApprove;
  final VoidCallback onReject;
  final VoidCallback? onOpen;

  const _ApprovalCard({
    required this.item,
    required this.busy,
    required this.onApprove,
    required this.onReject,
    this.onOpen,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: scheme.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: scheme.outlineVariant.withOpacity(0.5)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: scheme.primary.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(99),
                ),
                child: Text(
                  item.typeLabel.toUpperCase(),
                  style: TextStyle(
                    fontSize: 9.5,
                    fontWeight: FontWeight.w800,
                    color: scheme.primary,
                    letterSpacing: 0.4,
                  ),
                ),
              ),
              const Spacer(),
              Text(
                DateFormat('MMM d, h:mm a').format(item.createdAt.toLocal()),
                style: TextStyle(fontSize: 11, color: scheme.onSurfaceVariant),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(item.previewText, style: const TextStyle(fontSize: 14, height: 1.35)),
          if (item.requestedByName != null) ...[
            const SizedBox(height: 6),
            Text('Requested by ${item.requestedByName}',
                style: TextStyle(fontSize: 12, color: scheme.onSurfaceVariant)),
          ],
          if (onOpen != null) ...[
            const SizedBox(height: 8),
            InkWell(
              onTap: onOpen,
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text('Review full email',
                      style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: scheme.primary)),
                  Icon(Icons.chevron_right, size: 18, color: scheme.primary),
                ],
              ),
            ),
          ],
          const SizedBox(height: 12),
          if (busy)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 6),
              child: SizedBox(
                height: 20,
                width: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            )
          else
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: onReject,
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFFDC2626),
                      side: const BorderSide(color: Color(0x55DC2626)),
                    ),
                    icon: const Icon(Icons.close, size: 18),
                    label: const Text('Reject'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: FilledButton.icon(
                    onPressed: onApprove,
                    icon: const Icon(Icons.check, size: 18),
                    label: const Text('Approve'),
                  ),
                ),
              ],
            ),
        ],
      ),
    );
  }
}
