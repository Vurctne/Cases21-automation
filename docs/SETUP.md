# Setup (Phase A)

Done already: Premium trial, PC `AS-PC12EDTF` registered, flow `cases21-bridge-test` saved with an HTTP trigger.
Do the steps in order. Each ends with what to send back.

## 1. Put the stand-in on the PC

1. On github.com, open this repo, go to `standin/po-entry.html`, click **Download raw file** (the download icon).
2. Save it to **Documents**.
3. Open a new Edge window (**Ctrl+N**), drag the file into it. Keep this window open, with this tab active.
   The window title must start with `CASES21 stand-in`.

## 2. Desktop flow `cases21-hands`

DESKTOP_FLOW_SECTION

## 3. Cloud flow `cases21-bridge`

Reuse the test flow.

1. make.powerautomate.com > **My flows** > `cases21-bridge-test` > **Edit**.
2. Click the **When an HTTP request is received** box. In **Request Body JSON Schema** paste:
   ```json
   {"type": "object", "properties": {"steps": {"type": "array"}}, "required": ["steps"]}
   ```
3. Hover the arrow between the trigger and **Response**, click **+** > **Add an action**, search
   `Run a flow built with Power Automate for desktop`, click it.
   - Connection: if asked, **Connect with sign-in** > machine **AS-PC12EDTF** > **Sign in** with your school account.
   - **Desktop flow**: `cases21-hands`
   - **Run mode**: Attended
   - **StepsJson**: click in the box, click the **fx** icon, type `string(triggerBody())`, click **Add**.
4. Click the **Response** box.
   - **Status Code**: `200`
   - **Body**: type `{"error": "", "screenshot": ""}`. Put the cursor between the first pair of empty quotes,
     click the lightning icon, choose **Error** (under "Run a flow built with Power Automate for desktop").
     Put the cursor between the second pair, choose **ScreenshotB64** the same way.
   - **Settings** tab: turn **Asynchronous response** On.
5. Rename the flow (top left) to `cases21-bridge` and **Save**.

## 4. App registration (identity the agent signs in as)

It gets no API permissions. Its only use is to call the flow, once step 5 limits the flow to it.

1. entra.microsoft.com > **App registrations** > **+ New registration**.
   - Name: `cases21-bridge-agent`
   - Supported account types: **Accounts in this organizational directory only**
   - Redirect URI: leave empty. Click **Register**.
2. On **Overview**, note **Application (client) ID** and **Directory (tenant) ID**.
3. **Certificates & secrets** > **Client secrets** > **+ New client secret**: description `claude-cloud`,
   expires **90 days** > **Add**. Copy the **Value** now (it's shown once).
4. Back on **Overview**, click the link next to **Managed application in local directory**.
   Note the **Object ID** on that page (the service principal; not the one on the app registration page).

Never paste the secret into chat.

## 5. Lock the flow to the app

1. Edit `cases21-bridge`, click the trigger.
2. **Who can trigger the flow?** > **Specific users in my tenant**. In **Allowed users** paste the
   service principal **Object ID** from 4.4. (Left blank, any user in the tenant could call it.)
3. **Save**, then copy the **HTTP URL** from the trigger.

## 6. Give the agent its credentials

In the Claude app: the cloud environment menu in the session title bar > **Edit** > environment variables:

```
PA_TENANT_ID=<Directory (tenant) ID>
PA_CLIENT_ID=<Application (client) ID>
PA_CLIENT_SECRET=<secret Value>
PA_FLOW_URL=<HTTP URL>
```

Start a new session on this repo; it picks them up. Then tell Claude to run the end-to-end test:

```
python3 bridge/pa.py '{"steps": [{"type": "wait", "value": 1}]}'
```

Your PC must be unlocked and signed in, with the stand-in window open. Don't type while it runs.
