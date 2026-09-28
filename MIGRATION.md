# Moving the Dataverse dataset (and its DOI) to GitHub

## What can and can't be done with a DOI

A DOI can't be transferred to GitHub. Harvard Dataverse registered your DOI
(`10.7910/DVN/...`) through DataCite under Harvard's prefix, and only Harvard
Dataverse can change where it points. GitHub doesn't issue DOIs.

Dataverse DOIs are permanent, so the old DOI will keep working. The standard
approach has three parts:

1. **Move the data and metadata to GitHub.** The script in this repo does this.
2. **Get a new DOI for the GitHub version with Zenodo.** In the Zenodo
   metadata, the new DOI is recorded as `isNewVersionOf` the Dataverse DOI, so
   the two are linked in DataCite.
3. **Point the Dataverse record to GitHub.** Publish a new Dataverse version
   whose description says the dataset now lives on GitHub/Zenodo. You can
   optionally *deaccession* it; a deaccessioned DOI still resolves to a
   tombstone page, where you can leave a forwarding URL.

If you only need GitHub to host the data and are happy to keep citing the
Dataverse DOI, stop after step 1. `CITATION.cff` already tells people to cite
the original DOI.

## Step 1: Import the dataset (no local setup needed)

1. Push this branch and merge it into your default branch.
2. On GitHub, go to **Actions → "Migrate from Harvard Dataverse" → Run workflow**.
3. Enter your DOI, e.g. `doi:10.7910/DVN/ABC123`, and run it.
4. The workflow downloads every file (in its original upload format, not the
   `.tab` conversion Dataverse makes), saves the metadata, generates
   `CITATION.cff` and `.zenodo.json`, and commits them.

If any files are restricted, first add a Dataverse API token as a repository
secret named `DATAVERSE_API_TOKEN` (Settings → Secrets and variables →
Actions). You can create a token in Dataverse under your name → API Token.

To see the file list and sizes first, run the workflow with **"Only list the
files"** ticked. It prints each file's size and downloads nothing.

### Files over 100 MB

You don't need to check file sizes before running the import. GitHub refuses
to store files over 100 MB in the repository itself, so the workflow uploads
those files (up to 2 GB each) to a GitHub release named
`dataverse-large-files`. `metadata/LARGE_FILES_IN_RELEASE.txt` records each
file's original folder path. Any file over 2 GB is skipped and listed in
`metadata/SKIPPED_LARGE_FILES.txt`. For those files, either leave them on
Dataverse (the DOI still points there) or set up Git LFS.

To run it locally instead:

```
python3 scripts/migrate_from_dataverse.py doi:10.7910/DVN/ABC123 --list
python3 scripts/migrate_from_dataverse.py doi:10.7910/DVN/ABC123 --large-dir large_files
```

## Step 2: Mint a DOI for the GitHub version with Zenodo (optional)

1. Log in at <https://zenodo.org> with your GitHub account.
2. Go to **Account → GitHub** and switch this repository **On**.
3. On GitHub, create a Release (e.g. `v1.0.0`).
4. Zenodo archives the release and mints a DOI. It reads `.zenodo.json`, so
   the title, authors, license and the link to the Dataverse DOI are filled
   in automatically.
   Zenodo makes a new archived version only when you publish a GitHub
   Release, not on every push. Run the import **before** switching Zenodo on,
   so the automatic `dataverse-large-files` release doesn't get its own DOI.
   Zenodo archives only the repository contents, not files attached to a
   release. Large files stay on the GitHub release and on Dataverse.
5. Add the Zenodo **concept DOI**, which always resolves to the latest
   version, to `README.md` and as a second identifier in `CITATION.cff`.

## Step 3: Update the Dataverse record

In Dataverse, edit the dataset's metadata:

- Add a note to the description, e.g. "This dataset is now maintained at
  https://github.com/UncommonSense26/Empirical-Legal-Database (Zenodo DOI:
  10.5281/zenodo.XXXXXXX)."
- Under **Related Material** / **Related Datasets**, add the GitHub URL and
  the Zenodo DOI.
- Publish it as a new minor version.

Don't delete or deaccession the Dataverse dataset unless you need to. Existing
citations to the old DOI will keep landing on a page that points readers to
GitHub.
