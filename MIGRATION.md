# Moving the Dataverse dataset (and its DOI) to GitHub

## What can and can't be done with a DOI

A DOI can't be transferred to GitHub. Harvard Dataverse registered your DOI
(`10.7910/DVN/1D6ZDU`) through DataCite under Harvard's prefix, and only Harvard
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

1. Merge this branch into `main`.
2. On GitHub, go to **Actions → "Migrate from Harvard Dataverse" → Run workflow**.
   The DOI field is already set to `doi:10.7910/DVN/1D6ZDU`.
3. **Preview first.** Leave **"Preview only"** ticked (the default) and run it.
   The run's summary page shows every file, its size, and how many files go
   to each destination. Nothing is downloaded or committed.
4. **Import.** Run it again with **"Preview only"** unticked. The workflow:
   - commits files under 100 MB to `data/`, fetching the original upload
     format rather than the `.tab` conversion Dataverse makes;
   - uploads files from 100 MB to 2 GB to a release named `dataverse-large-files`;
   - lists files over 2 GB in `metadata/SKIPPED_LARGE_FILES.txt` without
     downloading them;
   - saves `metadata/dataverse_metadata.json` and `metadata/file_manifest.json`,
     checking every download against Dataverse's checksum;
   - replaces the placeholder `CITATION.cff` and `.zenodo.json` with the real
     title, authors, keywords, license, and abstract.

If any file fails to download, the run stops without committing anything,
so a partial import is never committed. The most likely cause is a
restricted file. In that case, add a Dataverse API token as a repository
secret named `DATAVERSE_API_TOKEN` (Settings → Secrets and variables →
Actions) and run the workflow again. You can create a token in Dataverse
under your name → API Token.

To run it locally instead:

```
python3 scripts/migrate_from_dataverse.py --list
python3 scripts/migrate_from_dataverse.py --large-dir large_files
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

## Step 3: Point the Dataverse record to GitHub

The DOI always resolves to the Dataverse landing page. That page is where
you redirect people to GitHub. In Dataverse, edit the dataset's metadata:

- Put a note at the top of the description, e.g. "This dataset is now maintained at
  https://github.com/UncommonSense26/Empirical-Legal-Database (Zenodo DOI:
  10.5281/zenodo.XXXXXXX)."
- Under **Related Material** / **Related Datasets**, add the GitHub URL and
  the Zenodo DOI.
- Publish it as a new minor version.

Don't delete or deaccession the Dataverse dataset unless you need to. Existing
citations to the old DOI will keep landing on a page that points readers to
GitHub.
