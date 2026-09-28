# Empirical Legal Database

[![DOI](https://img.shields.io/badge/DOI-10.7910%2FDVN%2F1D6ZDU-blue)](https://doi.org/10.7910/DVN/1D6ZDU)

This repository is the **primary, maintained source** of the Empirical Legal
Database. It was first published on Harvard Dataverse, and its DOI,
[10.7910/DVN/1D6ZDU](https://doi.org/10.7910/DVN/1D6ZDU), is permanent. The
Dataverse record points here.

## What's in this repository

| Location | Contents |
| --- | --- |
| `data/` | Dataset files under 100 MB, in their original upload format. The folder structure matches Dataverse. |
| [Release `dataverse-large-files`](../../releases/tag/dataverse-large-files) | Files from 100 MB to 2 GB. They're too large to store in the repository. |
| `metadata/file_manifest.json` | Every file's original path, size, checksum, and where it lives now. |
| `metadata/LARGE_FILES_IN_RELEASE.txt` | Maps each release file back to its original folder path. |
| `metadata/SKIPPED_LARGE_FILES.txt` | Files over 2 GB. These are only on Dataverse (with links). |
| `metadata/dataverse_metadata.json` | The complete original Dataverse metadata record. |
| `CITATION.cff` | Citation metadata. It powers GitHub's **"Cite this repository"** button. |

## Getting the data

**Everything except the large files:** click **Code → Download ZIP**, or run:

```
git clone https://github.com/UncommonSense26/Empirical-Legal-Database.git
```

**Large files (100 MB–2 GB):** download them from the
[`dataverse-large-files` release](../../releases/tag/dataverse-large-files),
or get them all at once with the [GitHub CLI](https://cli.github.com):

```
gh release download dataverse-large-files --repo UncommonSense26/Empirical-Legal-Database --dir large_files
```

Release files can't contain folders, so a file originally at
`folder/sub/file.zip` is named `folder__sub__file.zip`.
`metadata/LARGE_FILES_IN_RELEASE.txt` lists the original paths.

**Files over 2 GB:** download these from
[Harvard Dataverse](https://doi.org/10.7910/DVN/1D6ZDU). The links are in
`metadata/SKIPPED_LARGE_FILES.txt`.

**Checking your download:** each file's MD5 checksum from Dataverse is in
`metadata/file_manifest.json`. Compare it with `md5sum <file>` on Linux or
`md5 <file>` on macOS.

## Citing the dataset

Use GitHub's **"Cite this repository"** button in the sidebar for APA or BibTeX,
or cite:

> Empirical Legal Database. Harvard Dataverse. https://doi.org/10.7910/DVN/1D6ZDU

Once a Zenodo DOI for the GitHub version exists, it'll be listed here as
well. Both DOIs identify the same dataset.

## Maintainers

[MIGRATION.md](MIGRATION.md) explains how the dataset was imported from
Dataverse and how to connect Zenodo. It also covers updating the Dataverse
record so it points here.
