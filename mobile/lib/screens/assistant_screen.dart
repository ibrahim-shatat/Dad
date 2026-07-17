import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/api_client.dart';
import '../api/assistant_api.dart';
import '../models/chat.dart';
import '../state/auth_state.dart';

class _Turn {
  final String question;
  ChatResponse? answer;
  String? error;
  _Turn(this.question);
}

class AssistantScreen extends StatefulWidget {
  const AssistantScreen({super.key});

  @override
  State<AssistantScreen> createState() => _AssistantScreenState();
}

class _AssistantScreenState extends State<AssistantScreen> {
  final AssistantApi _api = AssistantApi(ApiClient());
  final TextEditingController _input = TextEditingController();
  final ScrollController _scroll = ScrollController();
  final List<_Turn> _turns = [];
  bool _busy = false;

  static const _suggestions = [
    'What needs my approval today?',
    'Summarize my open action items',
    'Any urgent emails I should see?',
  ];

  @override
  void dispose() {
    _input.dispose();
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _ask([String? preset]) async {
    final q = (preset ?? _input.text).trim();
    if (q.isEmpty || _busy) return;
    final token = context.read<AuthState>().token!;
    final turn = _Turn(q);
    setState(() {
      _turns.add(turn);
      _busy = true;
      _input.clear();
    });
    _scrollToBottom();
    try {
      final resp = await _api.ask(q, token);
      turn.answer = resp;
    } catch (e) {
      turn.error = e.toString();
    } finally {
      if (mounted) {
        setState(() => _busy = false);
        _scrollToBottom();
      }
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent,
            duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: const Text('Ask Dad')),
      body: Column(
        children: [
          Expanded(
            child: _turns.isEmpty
                ? _EmptyState(onPick: _ask, suggestions: _suggestions)
                : ListView.builder(
                    controller: _scroll,
                    padding: const EdgeInsets.fromLTRB(16, 16, 16, 16),
                    itemCount: _turns.length,
                    itemBuilder: (context, i) => _TurnView(turn: _turns[i]),
                  ),
          ),
          if (_busy)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const SizedBox(
                      height: 14, width: 14, child: CircularProgressIndicator(strokeWidth: 2)),
                  const SizedBox(width: 8),
                  Text('Thinking…', style: TextStyle(color: scheme.onSurfaceVariant)),
                ],
              ),
            ),
          SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 4, 12, 12),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _input,
                      minLines: 1,
                      maxLines: 4,
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => _ask(),
                      decoration: InputDecoration(
                        hintText: 'Ask about your emails, files, meetings…',
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(24)),
                        contentPadding:
                            const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  FilledButton(
                    onPressed: _busy ? null : () => _ask(),
                    style: FilledButton.styleFrom(
                      shape: const CircleBorder(),
                      padding: const EdgeInsets.all(14),
                    ),
                    child: const Icon(Icons.arrow_upward, size: 20),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  final void Function(String) onPick;
  final List<String> suggestions;
  const _EmptyState({required this.onPick, required this.suggestions});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        const SizedBox(height: 40),
        Icon(Icons.auto_awesome, size: 40, color: scheme.primary),
        const SizedBox(height: 12),
        Text('Ask across your emails, files, and meetings.',
            textAlign: TextAlign.center,
            style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 14)),
        const SizedBox(height: 24),
        ...suggestions.map((s) => Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: OutlinedButton(
                onPressed: () => onPick(s),
                style: OutlinedButton.styleFrom(
                  alignment: Alignment.centerLeft,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                ),
                child: Text(s),
              ),
            )),
      ],
    );
  }
}

class _TurnView extends StatelessWidget {
  final _Turn turn;
  const _TurnView({required this.turn});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Align(
          alignment: Alignment.centerRight,
          child: Container(
            margin: const EdgeInsets.only(bottom: 10, left: 40),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: scheme.primary,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Text(turn.question, style: const TextStyle(color: Colors.white)),
          ),
        ),
        if (turn.error != null)
          _bubble(context, 'Could not answer: ${turn.error}', scheme.errorContainer,
              scheme.onErrorContainer)
        else if (turn.answer != null) ...[
          _bubble(context, turn.answer!.answer, scheme.surface, scheme.onSurface,
              border: true),
          if (turn.answer!.sources.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(left: 4, bottom: 14, top: 2),
              child: Wrap(
                spacing: 6,
                runSpacing: 6,
                children: turn.answer!.sources
                    .map((s) => Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: scheme.primary.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(99),
                          ),
                          child: Text(s.label,
                              style: TextStyle(
                                  fontSize: 11,
                                  color: scheme.primary,
                                  fontWeight: FontWeight.w600)),
                        ))
                    .toList(),
              ),
            ),
        ],
      ],
    );
  }

  Widget _bubble(BuildContext context, String text, Color bg, Color fg,
          {bool border = false}) =>
      Align(
        alignment: Alignment.centerLeft,
        child: Container(
          margin: const EdgeInsets.only(bottom: 4, right: 40),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: bg,
            borderRadius: BorderRadius.circular(16),
            border: border
                ? Border.all(color: Theme.of(context).colorScheme.outlineVariant.withOpacity(0.5))
                : null,
          ),
          child: Text(text, style: TextStyle(color: fg, height: 1.4)),
        ),
      );
}
