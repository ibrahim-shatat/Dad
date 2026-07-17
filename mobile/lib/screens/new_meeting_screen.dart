import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/api_client.dart';
import '../api/meetings_api.dart';
import '../state/auth_state.dart';

/// Capture meeting notes on the go; the backend runs the AI extraction. Pops
/// `true` on success so the list can refresh.
class NewMeetingScreen extends StatefulWidget {
  const NewMeetingScreen({super.key});

  @override
  State<NewMeetingScreen> createState() => _NewMeetingScreenState();
}

class _NewMeetingScreenState extends State<NewMeetingScreen> {
  final MeetingsApi _api = MeetingsApi(ApiClient());
  final _formKey = GlobalKey<FormState>();
  final _title = TextEditingController();
  final _notes = TextEditingController();
  final _instructions = TextEditingController();
  bool _busy = false;

  @override
  void dispose() {
    _title.dispose();
    _notes.dispose();
    _instructions.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    FocusScope.of(context).unfocus();
    final token = context.read<AuthState>().token!;
    setState(() => _busy = true);
    try {
      await _api.create(
        title: _title.text.trim(),
        sourceText: _notes.text.trim(),
        instructions: _instructions.text,
        token: token,
      );
      if (!mounted) return;
      Navigator.of(context).pop(true);
    } catch (e) {
      if (!mounted) return;
      setState(() => _busy = false);
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Could not create meeting: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('New meeting')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
          children: [
            TextFormField(
              controller: _title,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(
                labelText: 'Title',
                hintText: 'e.g. Site A weekly sync',
              ),
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? 'Give the meeting a title' : null,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _notes,
              minLines: 6,
              maxLines: 14,
              textCapitalization: TextCapitalization.sentences,
              decoration: const InputDecoration(
                labelText: 'Notes / transcript',
                hintText: 'Paste or type what was discussed…',
                alignLabelWithHint: true,
              ),
              validator: (v) =>
                  (v == null || v.trim().length < 10) ? 'Add the meeting notes' : null,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _instructions,
              minLines: 1,
              maxLines: 3,
              decoration: const InputDecoration(
                labelText: 'Instructions (optional)',
                hintText: 'e.g. focus on decisions and owners',
              ),
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: _busy ? null : _submit,
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              icon: _busy
                  ? const SizedBox(
                      height: 18,
                      width: 18,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Icon(Icons.auto_awesome, size: 18),
              label: Text(_busy ? 'Creating…' : 'Create & analyze'),
            ),
            const SizedBox(height: 12),
            Text(
              'The AI will extract a summary, action items, and decisions. It appears in the '
              'list in a moment — pull to refresh.',
              style: TextStyle(
                fontSize: 12.5,
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
