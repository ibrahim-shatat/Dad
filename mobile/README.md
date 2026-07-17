# Dad — Mobile App (Flutter)

The native mobile client for Dad. It talks to the **same backend API** as the web app
(`https://dad-api-rw61.onrender.com`), so all AI, auth, and data logic is shared — this is
just the phone front-end.

**Phase 1 (this scaffold):** sign in + the "Prepare My Day" dashboard (the priority-ranked
attention feed and key counters), pulled live from `GET /dashboard`.

## What's here

```
mobile/
  pubspec.yaml          dependencies
  lib/
    main.dart           app entry + auth routing
    config.dart         API base URL (override with --dart-define)
    theme.dart          indigo Material 3 theme (matches the web app)
    api/                api_client, auth_api, dashboard_api
    models/             user, attention_item, dashboard_summary
    state/              auth_state (secure-storage token session)
    screens/            login_screen, dashboard_screen
    widgets/            attention_row
```

Only `lib/`, `pubspec.yaml`, and this README are committed. The platform folders
(`android/`, `ios/`, …) are generated locally — see step 2.

## Prerequisites (one-time)

1. **Install Flutter** — https://docs.flutter.dev/get-started/install (includes Dart).
   Then check your setup:
   ```bash
   flutter doctor
   ```
2. For **Android**: install Android Studio (gives you the Android SDK + an emulator).
   For **iOS** (Mac only): install Xcode.

## Build & run

```bash
cd mobile

# 2. Generate the native platform folders around this code.
#    (This may overwrite pubspec.yaml / lib/main.dart with Flutter's template…)
flutter create --project-name dad_mobile --org com.dadassistant --platforms=android,ios .

# 3. …so restore our app code from git (keeps the generated android/ios folders):
git checkout -- lib pubspec.yaml

# 4. Fetch packages and run on a connected phone or emulator.
flutter pub get
flutter run
```

The app defaults to the live Render API. To point it at a local backend instead
(e.g. the Android emulator reaching your PC), pass:

```bash
flutter run --dart-define=DAD_API_URL=http://10.0.2.2:8000/api/v1
```

## Ship to a phone

- **Android (share an APK your dad can install):**
  ```bash
  flutter build apk --release
  # → build/app/outputs/flutter-apk/app-release.apk  (send this file)
  ```
- **iOS / App Store & Android Play Store:** needs paid Apple/Google developer accounts;
  we'll wire that up in a later phase.

## Roadmap

This is Phase 1. Next for the app: email inbox, approvals (approve/reject on the go),
push notifications, and the rest of the dashboard tabs — each reusing the existing API.
