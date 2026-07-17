import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/api_client.dart';
import '../api/documents_api.dart';
import '../models/document.dart';
import '../state/auth_state.dart';
import 'document_detail_screen.dart';

class DocumentsScreen extends StatefulWidget {
  const DocumentsScreen({super.key});

  @override
  State<DocumentsScreen> createState() => _DocumentsScreenState();
}

class _DocumentsScreenState extends State<DocumentsScreen> {
  final DocumentsApi _api = DocumentsApi(ApiClient());
  late Future<List<Document>> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<List<Document>> _load() {
    final token = context.read<AuthState>().token!;
    return _api.list(token);
  }

  bool _uploading = false;

  Future<void> _refresh() async {
    final next = _load();
    setState(() => _future = next);
    try {
      await next;
    } catch (_) {}
  }

  Future<void> _upload() async {
    if (_uploading) return;
    final picked = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: DocumentsApi.allowedExtensions,
      withData: false,
    );
    if (picked == null || picked.files.isEmpty) return;
    final file = picked.files.first;
    if (file.path == null) return;

    final token = context.read<AuthState>().token!;
    setState(() => _uploading = true);
    try {
      await _api.upload(filePath: file.path!, filename: file.name, token: token);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Uploaded — AI review starting. Pull to refresh shortly.')),
      );
      await _refresh();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Upload failed: $e')));
    } finally {
      if (mounted) setState(() => _uploading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Documents')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _uploading ? null : _upload,
        icon: _uploading
            ? const SizedBox(
                height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2))
            : const Icon(Icons.upload_file),
        label: Text(_uploading ? 'Uploading…' : 'Upload'),
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<Document>>(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState == ConnectionState.waiting) {
              return ListView(children: const [
                SizedBox(height: 120),
                Center(child: CircularProgressIndicator()),
              ]);
            }
            if (snap.hasError) {
              return _centered(context, 'Could not load documents.\n${snap.error}');
            }
            final docs = snap.data!;
            if (docs.isEmpty) {
              return _centered(
                  context, 'No documents yet.\nUpload one from the web console to get a review.');
            }
            return ListView.builder(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 24),
              itemCount: docs.length,
              itemBuilder: (context, i) => _DocumentCard(doc: docs[i]),
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

Color documentStatusColor(String status) {
  switch (status) {
    case 'reviewed':
      return const Color(0xFF15864B);
    case 'failed':
      return const Color(0xFFDC2626);
    default:
      return const Color(0xFFD97706); // uploaded / extracting / reviewing
  }
}

class _DocumentCard extends StatelessWidget {
  final Document doc;
  const _DocumentCard({required this.doc});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final riskCount = doc.review?.riskFlags.length ?? 0;
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
          MaterialPageRoute(builder: (_) => DocumentDetailScreen(doc: doc)),
        ),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: scheme.primary.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(Icons.description_outlined, color: scheme.primary, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(doc.filename,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 3),
                    Text(
                      [
                        doc.sizeLabel,
                        if (riskCount > 0) '$riskCount risk${riskCount == 1 ? '' : 's'} flagged',
                      ].join('  ·  '),
                      style: TextStyle(fontSize: 12, color: scheme.onSurfaceVariant),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              _chip(doc.status, documentStatusColor(doc.status)),
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
                fontSize: 9, fontWeight: FontWeight.w800, color: color, letterSpacing: 0.3)),
      );
}
