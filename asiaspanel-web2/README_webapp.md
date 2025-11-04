# Deploying the Static Web App (step‑by‑step)

This document explains how to create a simple static web app (an `index.html` page), deploy it to Azure Static Web Apps using the GitHub Actions workflow that Azure creates, obtain the public URL, and how to change the page and redeploy.

The instructions use PowerShell/ VS Code on Windows. Adjust command syntax for other shells.

---

## 1) Create the app folder and index.html (local)

From the repository root create the folder the workflow will upload and add a simple `index.html`:

```powershell
# create folder (example name used in this repo)
mkdir asiaspanel-web2

# create a minimal index.html
Set-Content -Path asiaspanel-web2\index.html -Value '<!doctype html><html><head><meta charset="utf-8"><title>asiaspanel-web2</title></head><body><h1>asiaspanel-web2 - Hello</h1></body></html>'

# quick local preview (optional)
cd asiaspanel-web2
python -m http.server 8000    # open http://localhost:8000
```

If you already have your site files (CSS, JS, images), place them under `asiaspanel-web2/`.

---

## 2) Confirm the GitHub Actions workflow config

When you created the Static Web App in the Azure portal (or through the Azure tools), Azure added a workflow file under `.github/workflows/`.
Open that file and locate these three values:

- `on.push.branches` — the branch name the workflow runs on (e.g., `master` or `main`).
- `app_location` — the repository path containing your static files (set it to `asiaspanel-web2` if you used that folder).
- `output_location` — where the build step expects the built files. For pure static sites set this to `.` (the folder itself) or adjust it to where your build writes files.

If you need to change the workflow to use `asiaspanel-web2`, edit `.github/workflows/<your-workflow>.yml` and set:

```yaml
app_location: "asiaspanel-web2"
api_location: ""        # if you don't have serverless APIs
output_location: "."    # upload files from the folder directly
```

Commit changes to that workflow and push to the branch the Action listens to.

---

## 3) Commit and push to trigger GitHub Actions (deploy)

Make sure you're on the branch the workflow watches (example uses `master`):

```powershell
# ensure you are on the correct branch
git checkout master

git add asiaspanel-web2
git commit -m "Add static site files for asiaspanel-web2"
git push origin master
```

Pushing to the configured branch triggers the `Azure/static-web-apps-deploy` action in the workflow. Open your repository on GitHub → Actions to follow the job logs.

---

## 4) Get the deployed URL

When the Actions job completes successfully it usually prints the deployed URL in the job summary and logs. There are two more ways to obtain the URL:

1) Azure CLI (replace names with your resource name / resource group):

```powershell
az staticwebapp show --name <APP_NAME> --resource-group <RESOURCE_GROUP> --query defaultHostname -o tsv
# open in default browser (PowerShell)
$host = az staticwebapp show --name <APP_NAME> --resource-group <RESOURCE_GROUP> --query defaultHostname -o tsv
start "https://$host"
```

2) Azure Portal: Static Web Apps → select your app → Overview → the URL.

Typical URL is: `https://<generated-name>.azurestaticapps.net` or `https://<hostname>.3.azurestaticapps.net`.

---

## 5) Modify `index.html` and redeploy

Change the file locally, commit and push to the same branch — the workflow will redeploy automatically.

```powershell
# edit the file (use your editor) then:
git add asiaspanel-web2/index.html
git commit -m "Update landing page"
git push origin master
```

Wait for the GitHub Actions job to complete and refresh the site URL in your browser.

Notes:
- If you prefer to test changes before pushing, run a local server (see step 1).
- If your workflow includes a build step (for frameworks) make sure `output_location` matches the build output directory (for example `build` or `dist`).

---

## 6) Troubleshooting

- Workflow didn't find files / deployment fails: check `app_location` and `output_location` in the workflow YAML and make sure the GitHub Actions job has access to the folder you added.
- 403 / resource not found errors: confirm you are using the right Azure subscription/tenant and that the Azure credential used by the action has permissions to the Static Web App resource.
- Deployment URL still shows old content: GitHub Actions may take a minute to complete — check the Actions logs and redeploy if necessary.

---

If you'd like, I can also:
- update the workflow in the repo to match a different `app_location`/`output_location` (I already updated this repo to use `asiaspanel-web2`), or
- copy files into the `dist/` folder the workflow originally expected instead of changing the workflow.

Happy to perform either change for you — tell me which behavior you prefer.
