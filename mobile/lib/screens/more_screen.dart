import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../state/auth_state.dart';
import 'assistant_screen.dart';
import 'briefing_screen.dart';
import 'documents_screen.dart';
import 'meetings_screen.dart';

/// Secondary sections that don't fit on the bottom bar, plus the account/logout.
class MoreScreen extends StatelessWidget {
  const MoreScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthState>();
    final scheme = Theme.of(context).colorScheme;

    void open(Widget screen) => Navigator.of(context)
        .push(MaterialPageRoute(builder: (_) => screen));

    return Scaffold(
      appBar: AppBar(title: const Text('More')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(12, 8, 12, 24),
        children: [
          _Row(
            icon: Icons.auto_awesome,
            label: 'Ask Dad',
            subtitle: 'Ask across emails, files, and meetings',
            onTap: () => open(const AssistantScreen()),
          ),
          _Row(
            icon: Icons.wb_sunny_outlined,
            label: 'Daily briefing',
            subtitle: 'Your executive summary for today',
            onTap: () => open(const BriefingScreen()),
          ),
          _Row(
            icon: Icons.groups_outlined,
            label: 'Meetings',
            subtitle: 'Summaries, action items, decisions',
            onTap: () => open(const MeetingsScreen()),
          ),
          _Row(
            icon: Icons.folder_outlined,
            label: 'Documents',
            subtitle: 'Reviews, risks, suggested rewrites',
            onTap: () => open(const DocumentsScreen()),
          ),
          const SizedBox(height: 20),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: scheme.surface,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: scheme.outlineVariant.withOpacity(0.5)),
            ),
            child: Row(
              children: [
                CircleAvatar(
                  backgroundColor: scheme.primary.withOpacity(0.12),
                  child: Text(
                    _initials(auth.user?.fullName),
                    style: TextStyle(color: scheme.primary, fontWeight: FontWeight.bold),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(auth.user?.fullName ?? '',
                          style: const TextStyle(fontWeight: FontWeight.w600)),
                      Text(auth.user?.role ?? '',
                          style: TextStyle(
                              fontSize: 12, color: scheme.onSurfaceVariant)),
                    ],
                  ),
                ),
                TextButton.icon(
                  onPressed: () => auth.logout(),
                  icon: const Icon(Icons.logout, size: 18),
                  label: const Text('Log out'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _initials(String? name) {
    final n = (name ?? '').trim();
    if (n.isEmpty) return '?';
    final parts = n.split(' ').where((p) => p.isNotEmpty).toList();
    if (parts.length == 1) return parts.first[0].toUpperCase();
    return (parts.first[0] + parts.last[0]).toUpperCase();
  }
}

class _Row extends StatelessWidget {
  final IconData icon;
  final String label;
  final String subtitle;
  final VoidCallback onTap;

  const _Row({
    required this.icon,
    required this.label,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: scheme.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: scheme.outlineVariant.withOpacity(0.5)),
      ),
      child: ListTile(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        leading: Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: scheme.primary.withOpacity(0.1),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(icon, color: scheme.primary, size: 20),
        ),
        title: Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text(subtitle),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}
