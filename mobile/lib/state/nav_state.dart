import 'package:flutter/foundation.dart';

/// The selected bottom-nav tab, shared so screens (e.g. the dashboard's attention
/// feed) can jump to another tab.
class NavState extends ChangeNotifier {
  int index = 0;

  // Bottom-tab indices, named for clarity.
  static const today = 0;
  static const email = 1;
  static const approvals = 2;
  static const calendar = 3;
  static const more = 4;

  void go(int i) {
    if (i == index) return;
    index = i;
    notifyListeners();
  }
}
