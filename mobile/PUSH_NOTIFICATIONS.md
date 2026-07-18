# Push notifications — setup

Native push uses **Firebase Cloud Messaging (FCM)**. This is a one-time setup that produces two
artifacts:

1. **`google-services.json`** — configures the Android app (the client that receives pushes).
2. **A service-account key (JSON)** — lets the backend *send* pushes.

Everything below is free.

## 1. Create the Firebase project
1. Go to <https://console.firebase.google.com> → **Add project** → name it **Dad** → continue
   (you can disable Google Analytics) → create.

## 2. Add the Android app (gives `google-services.json`)
1. In the project, click the **Android** icon ("Add app").
2. **Android package name:** `com.dadassistant.dad_mobile`  ← must match exactly.
3. App nickname: `Dad` (optional). Register.
4. **Download `google-services.json`.** Keep it — you'll hand it to me (see step 5).
5. Skip the remaining "add SDK" steps in the wizard (I do that in code/CI).

## 3. Get the backend sender key (service account)
1. Firebase console → gear icon → **Project settings** → **Service accounts** tab.
2. Click **Generate new private key** → **Generate key** → a `.json` file downloads.
   *(This is a secret — treat it like a password.)*
3. Also note the **Project ID** (Project settings → General → "Project ID").

## 4. Configure the backend (Render)
In the Render dashboard → dad-api → **Environment**, add:

| Key | Value |
|-----|-------|
| `FCM_PROJECT_ID` | the Firebase **Project ID** |
| `FCM_CREDENTIALS_JSON` | paste the **entire contents** of the service-account `.json` from step 3 |

Save → Render redeploys. (With these empty, everything still works — there's just no mobile push.)

## 5. Hand me the app config
So I can wire the Flutter side and the cloud build, do **one** of:
- **Preferred:** add a GitHub **repository secret** named `GOOGLE_SERVICES_JSON` whose value is the
  full contents of `google-services.json` (repo → Settings → Secrets and variables → Actions →
  New repository secret). The build injects it automatically and it never lands in git.
- Or paste me the `google-services.json` contents and I'll take it from there.

## What happens after
Once the backend has its keys and I've wired the app + CI:
- On first login the app registers its device with `POST /push/devices`.
- Any notification the system already raises (a pending approval, etc.) also pushes to the phone.
- Tapping a push opens the app (deep-linking to the right screen comes next).
