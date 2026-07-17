import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../state/nav_state.dart';
import 'approvals_screen.dart';
import 'calendar_screen.dart';
import 'dashboard_screen.dart';
import 'email_screen.dart';
import 'more_screen.dart';

/// The signed-in app. The five daily-driver sections live on the bottom bar;
/// deeper sections (Meetings, Documents, Briefing, Assistant) sit under "More".
/// Tabs are kept alive in an IndexedStack so switching doesn't refetch.
class HomeShell extends StatelessWidget {
  const HomeShell({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => NavState(),
      child: const _HomeShellBody(),
    );
  }
}

class _HomeShellBody extends StatelessWidget {
  const _HomeShellBody();

  static const _pages = [
    DashboardScreen(),
    EmailScreen(),
    ApprovalsScreen(),
    CalendarScreen(),
    MoreScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    final index = context.watch<NavState>().index;
    return Scaffold(
      body: IndexedStack(index: index, children: _pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (i) => context.read<NavState>().go(i),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard),
            label: 'Today',
          ),
          NavigationDestination(
            icon: Icon(Icons.mail_outline),
            selectedIcon: Icon(Icons.mail),
            label: 'Email',
          ),
          NavigationDestination(
            icon: Icon(Icons.task_alt_outlined),
            selectedIcon: Icon(Icons.task_alt),
            label: 'Approvals',
          ),
          NavigationDestination(
            icon: Icon(Icons.calendar_today_outlined),
            selectedIcon: Icon(Icons.calendar_today),
            label: 'Calendar',
          ),
          NavigationDestination(
            icon: Icon(Icons.menu),
            selectedIcon: Icon(Icons.menu),
            label: 'More',
          ),
        ],
      ),
    );
  }
}
