
---

## 2. 12-Step Azure Implementation Outline

### Step 1 – Sign In
Log into [https://portal.azure.com](https://portal.azure.com) with your Microsoft account.

### Step 2 – Confirm Subscription
Check **Subscriptions → Pay-As-You-Go → Status: Active**.

### Step 3 – Create Resource Group
- Name: `rg-asiaspanel-dev`  
- Region: *Switzerland North* / *West Europe*

### Step 4 – Create Storage Account
- Name: `stasiaspaneldev`  
- Region: same as RG  
- Performance: Standard  
- Redundancy: LRS

### Step 5 – Create Static Web App (frontend)
- Name: `asiaspanel-web`  
- Plan: Free  
- Region: Europe  
- Deployment source: Other / No source  
→ yields URL `https://<random>.azurestaticapps.net`

### Step 6 – Create Function App (backend)
- Name: `func-asiaspanel-dev`  
- Runtime stack: **Node 20 (Node.js)**  
- Plan type: **Flex Consumption**  
- Auth type: **Secrets**  
- Storage account: `stasiaspaneldev`  
→ hosts backend logic / OpenAI API calls.

### Step 7 – Prepare VS Code (optional)
Install **Azure Tools** extension pack (`ms-vscode.vscode-azureextensionpack`) and sign in if possible.

### Step 8 – Create Frontend Locally
`index.html`
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Asia's Panel</title>
</head>
<body>
  <h1>Asia's Panel</h1>
  <p>Select a voice:</p>
  <select id="voiceSelect"></select>
  <button id="testBtn">Test Voice</button>
  <script>
    async function loadVoices() {
      const res = await fetch("https://func-asiaspanel-dev.azurewebsites.net/api/GetVoices");
      const voices = await res.json();
      const sel = document.getElementById("voiceSelect");
      voices.forEach(v => {
        const o = document.createElement("option");
        o.value = v.id; o.textContent = v.label;
        sel.appendChild(o);
      });
    }
    loadVoices();
  </script>
</body>
</html>
