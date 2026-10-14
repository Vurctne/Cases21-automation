# Setup (Phase A)

Done already: Premium trial, PC `AS-PC12EDTF` registered, flow `cases21-bridge-test` saved with an HTTP trigger.
Do the steps in order. Each ends with what to send back.

## 1. Put the stand-in on the PC

1. On github.com, open this repo, go to `standin/po-entry.html`, click **Download raw file** (the download icon).
2. Save it to **Documents**.
3. Open a new Edge window (**Ctrl+N**), drag the file into it. Keep this window open, with this tab active.
   The window title must start with `CASES21 stand-in`.

## 2. Desktop flow `cases21-hands`

This flow is the only part that touches the PC. It does nothing unless a window titled
`CASES21 stand-in...` exists, re-focuses that window before every step, and screenshots only that window.

1. Open **Power Automate for desktop** > **+ New flow**. Name: `cases21-hands`.
   If the dialog shows a **Power Fx enabled** option, turn it **off** (the code below won't paste otherwise).
   Click **Create**.
2. In the **Variables** panel (right) > **Input / output variables** > **+**:
   - **Input**: name `StepsJson`, type Text, default value `{"steps": [{"type": "keys", "value": "ACME01{Tab}"}]}`,
     external name `StepsJson` > **Save**.
   - **Output**: name `ScreenshotB64`, type Text, external name `ScreenshotB64` > **Save**.
   - **Output**: name `ErrorText`, type Text, external name `ErrorText` > **Save**.
3. Copy all the code below, click in the empty middle area of the designer, press **Ctrl+V**.
   If nothing appears, PAD rejected a line: send Claude a screenshot.
   ```
   SET ErrorText TO $''''''
   SET ScreenshotB64 TO $''''''
   SET Done TO False
   BLOCK 
   ON BLOCK ERROR all
   END
       Variables.ConvertJsonToCustomObject Json: StepsJson CustomObject=> Job
       LOOP FOREACH Step IN Job['steps']
           UIAutomation.FocusWindow.FocusByTitleClass Title: $'''CASES21 stand-in*''' Class: $''''''
           IF Step['type'] = $'''keys''' THEN
               SET Keys TO Step['value']
               MouseAndKeyboard.SendKeys.FocusAndSendKeys TextToSend: Keys DelayBetweenKeystrokes: 20 SendTextAsHardwareKeys: False
           ELSE IF Step['type'] = $'''click''' THEN
               SET ClickX TO Step['x']
               SET ClickY TO Step['y']
               MouseAndKeyboard.SendMouseClick.ClickAt ClickType: MouseAndKeyboard.MouseClickType.LeftClick MillisecondsDelay: 0 X: ClickX Y: ClickY RelativeTo: MouseAndKeyboard.PositionRelativeTo.ActiveWindow MovementStyle: MouseAndKeyboard.MovementStyle.Instant
           ELSE IF Step['type'] = $'''wait''' THEN
               SET Seconds TO Step['value']
               WAIT Seconds
           END
       END
       SET Done TO True
   END
   IF Done = False THEN
       ERROR => LastError
       SET ErrorText TO LastError.Message
   END
   BLOCK 
   ON BLOCK ERROR all
   END
       WAIT 1
       UIAutomation.FocusWindow.FocusByTitleClass Title: $'''CASES21 stand-in*''' Class: $''''''
       System.GetEnvironmentVariable.GetEnvironmentVariable Name: $'''TEMP''' Value=> TempDir
       SET ShotPath TO $'''%TempDir%\\cases21-shot.jpg'''
       Workstation.TakeScreenshot.TakeScreenshotOfForegroundWindowAndSaveToFile File: ShotPath ImageFormat: System.ImageFormat.Jpg
       File.ConvertToBase64 File: ShotPath Base64Text=> ScreenshotB64
   END
   ```
4. **Ctrl+S**. With the stand-in window open, click **Run** (▶). Expected: the stand-in's Creditor code
   shows `ACME01`, the cursor moves to Order date, and in the Variables panel `ScreenshotB64` is a long
   text and `ErrorText` is empty. Send Claude a screenshot of the Variables panel.

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
     click the lightning icon, choose **ErrorText** (under "Run a flow built with Power Automate for desktop").
     Put the cursor between the second pair, choose **ScreenshotB64** the same way.
   - Leave **Asynchronous response** (Settings tab) off. The agent then gets the answer in the same call,
     which must finish within 2 minutes.
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
