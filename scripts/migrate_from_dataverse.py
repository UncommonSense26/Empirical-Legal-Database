#!/usr/bin/env python3
"""Copy the Empirical Legal Database from Harvard Dataverse into this repository.

Downloads every file in the latest published version of the dataset and
sorts them by size:

    under 100 MB   -> data/ (committed to the repository)
    100 MB - 2 GB  -> --large-dir (uploaded to the "dataverse-large-files" release)
    over 2 GB      -> not downloaded, logged in metadata/SKIPPED_LARGE_FILES.txt

It also saves the full Dataverse metadata and a file manifest with checksums,
and regenerates CITATION.cff and .zenodo.json from the real dataset metadata.

Usage:
    python scripts/migrate_from_dataverse.py --list                 # preview only
    python scripts/migrate_from_dataverse.py --large-dir large_files
    python scripts/migrate_from_dataverse.py doi:10.7910/DVN/OTHER  # another dataset

Set DATAVERSE_API_TOKEN (or pass --api-token) if any files are restricted.
Standard library only (Python 3.8+).
"""
import argparse
import hashlib
import json
import os
import re
import sys
import urllib.parse
import urllib.request

DEFAULT_DOI = "doi:10.7910/DVN/1D6ZDU"
DEFAULT_REPO = "UncommonSense26/Empirical-Legal-Database"
SERVER = "https://dataverse.harvard.edu"
REPO_LIMIT = 100 * 1024 * 1024  # GitHub rejects committed files over 100 MB
RELEASE_LIMIT = 2 * 1024 * 1024 * 1024  # GitHub release assets max out at 2 GB
RELEASE_TAG = "dataverse-large-files"


def open_url(url, token=None):
    req = urllib.request.Request(url, headers={"User-Agent": "dataverse-to-github"})
    if token:
        req.add_header("X-Dataverse-key", token)
    return urllib.request.urlopen(req)


def get_json(url, token=None):
    with open_url(url, token) as resp:
        return json.load(resp)


def download(url, dest, token=None, algorithm=None):
    """Stream url to dest; return the file's hex digest if an algorithm is given."""
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    digest = hashlib.new(algorithm) if algorithm else None
    with open_url(url, token) as resp, open(dest, "wb") as out:
        while chunk := resp.read(1 << 20):
            out.write(chunk)
            if digest:
                digest.update(chunk)
    return digest.hexdigest() if digest else None


def field(citation, name):
    for f in citation.get("fields", []):
        if f["typeName"] == name:
            return f["value"]
    return None


def yaml_str(s):
    return json.dumps(s or "", ensure_ascii=False)


def split_name(full):
    # Dataverse stores authors as "Last, First"
    if "," in full:
        last, first = [p.strip() for p in full.split(",", 1)]
        return last, first
    parts = full.split()
    return parts[-1], " ".join(parts[:-1])


def human(size):
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{size} B"
        size /= 1024


def file_info(entry):
    df = entry["dataFile"]
    # Tabular uploads are converted to .tab by Dataverse; fetch the original instead
    original = bool(df.get("originalFileName"))
    name = df["originalFileName"] if original else df["filename"]
    size = (df.get("originalFileSize") if original else None) or df.get("filesize") or 0
    return {
        "id": df["id"],
        "path": os.path.join(entry.get("directoryLabel") or "", name),
        "size": size,
        "original": original,
        "restricted": bool(entry.get("restricted")),
        "checksum": df.get("checksum") or ({"type": "MD5", "value": df["md5"]} if df.get("md5") else None),
    }


def category(size):
    if size <= REPO_LIMIT:
        return "repo"
    if size <= RELEASE_LIMIT:
        return "release"
    return "skipped"


def write_citation(meta, version, bare_doi, repo_url):
    cit = version["metadataBlocks"]["citation"]
    title = field(cit, "title") or "Empirical Legal Database"
    authors = [a["authorName"]["value"] for a in field(cit, "author") or []]
    desc = " ".join(d["dsDescriptionValue"]["value"] for d in field(cit, "dsDescription") or [])
    desc = re.sub(r"<[^>]+>", "", desc).strip()
    keywords = [k["keywordValue"]["value"] for k in field(cit, "keyword") or [] if "keywordValue" in k]
    license_name = (version.get("license") or {}).get("name", "")
    released = (version.get("releaseTime") or meta.get("publicationDate") or "")[:10]
    version_str = f"{version.get('versionNumber', '')}.{version.get('versionMinorNumber', '')}".strip(".")

    cff_license = zen_license = None
    if license_name.startswith("CC0"):
        cff_license, zen_license = "CC0-1.0", "cc-zero"
    elif license_name.startswith("CC BY"):
        cff_license, zen_license = "CC-BY-4.0", "cc-by-4.0"

    lines = [
        "cff-version: 1.2.0",
        'message: "If you use this dataset, please cite it using the metadata below."',
        "type: dataset",
        f"title: {yaml_str(title)}",
        "authors:",
    ]
    for a in authors:
        last, first = split_name(a)
        lines.append(f"  - family-names: {yaml_str(last)}")
        if first:
            lines.append(f"    given-names: {yaml_str(first)}")
    if not authors:
        lines.append('  - name: "Empirical Legal Database contributors"')
    lines += [
        f"doi: {bare_doi}",
        f"url: {yaml_str(repo_url)}",
        f"repository: {yaml_str(repo_url)}",
        "identifiers:",
        "  - type: doi",
        f"    value: {bare_doi}",
        '    description: "Harvard Dataverse DOI (permanent; the dataset is now maintained on GitHub)"',
        "  - type: url",
        f"    value: {yaml_str(repo_url)}",
        '    description: "Primary source: GitHub repository"',
    ]
    if version_str:
        lines.append(f"version: {yaml_str('dataverse-' + version_str)}")
    if released:
        lines.append(f"date-released: {released}")
    if cff_license:
        lines.append(f"license: {cff_license}")
    if keywords:
        lines.append("keywords:")
        lines += [f"  - {yaml_str(k)}" for k in keywords]
    if desc:
        lines.append(f"abstract: {yaml_str(desc)}")
    with open("CITATION.cff", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    zenodo = {
        "upload_type": "dataset",
        "title": title,
        "creators": [{"name": a} for a in authors] or [{"name": "Empirical Legal Database contributors"}],
        "description": desc or title,
        # Zenodo adds the GitHub repository link itself
        "related_identifiers": [
            {"identifier": bare_doi, "relation": "isNewVersionOf", "scheme": "doi",
             "resource_type": "dataset"},
        ],
    }
    if keywords:
        zenodo["keywords"] = keywords
    if zen_license:
        zenodo["license"] = zen_license
    with open(".zenodo.json", "w", encoding="utf-8") as f:
        json.dump(zenodo, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("doi", nargs="?", default=DEFAULT_DOI, help=f"dataset DOI (default {DEFAULT_DOI})")
    ap.add_argument("--server", default=SERVER)
    ap.add_argument("--api-token", default=os.environ.get("DATAVERSE_API_TOKEN") or None)
    ap.add_argument("--out", default="data", help="directory for files under 100 MB")
    ap.add_argument("--large-dir", help="download 100 MB-2 GB files here for the release "
                                        "(without it they are logged but not downloaded)")
    ap.add_argument("--list", action="store_true", help="preview files, sizes and counts; download nothing")
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY") or DEFAULT_REPO)
    args = ap.parse_args()

    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", args.doi.strip())
    if not doi.startswith("doi:"):
        doi = "doi:" + doi
    bare_doi = doi[4:]
    repo_url = f"https://github.com/{args.repo}"

    pid = urllib.parse.quote(doi, safe="")
    meta = get_json(f"{args.server}/api/datasets/:persistentId/?persistentId={pid}", args.api_token)["data"]
    version = meta["latestVersion"]
    files = [file_info(e) for e in version.get("files", [])]

    groups = {"repo": [], "release": [], "skipped": []}
    for f in files:
        groups[category(f["size"])].append(f)

    labels = {"repo": "Repository (under 100 MB)",
              "release": f"Release '{RELEASE_TAG}' (100 MB-2 GB)",
              "skipped": "Skipped, logged only (over 2 GB)"}
    print(f"Dataset {doi}, version {version.get('versionNumber')}.{version.get('versionMinorNumber')}")
    for key, items in groups.items():
        print(f"\n{labels[key]}: {len(items)} files, {human(sum(f['size'] for f in items))}")
        for f in items:
            print(f"  {human(f['size']):>10}  {f['path']}{'  [restricted]' if f['restricted'] else ''}")
    print(f"\nTotal: {len(files)} files, {human(sum(f['size'] for f in files))}")
    if args.list:
        if any(f["restricted"] for f in files) and not args.api_token:
            print("\nNote: restricted files need a DATAVERSE_API_TOKEN to download.")
        return 0

    os.makedirs("metadata", exist_ok=True)
    with open("metadata/dataverse_metadata.json", "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)

    manifest, mismatches, failures = [], [], []
    for f in files:
        cat = category(f["size"])
        if cat == "skipped" or (cat == "release" and not args.large_dir):
            location = "not downloaded (see Dataverse)"
        else:
            if cat == "repo":
                dest = os.path.join(args.out, f["path"])
                location = dest
            else:
                # release assets are flat, so encode the folder into the file name
                asset = f["path"].replace("/", "__")
                dest = os.path.join(args.large_dir, asset)
                location = f"release {RELEASE_TAG}: {asset}"
            url = f"{args.server}/api/access/datafile/{f['id']}"
            if f["original"]:
                url += "?format=original"
            algo = (f["checksum"] or {}).get("type", "").lower().replace("-", "")
            algo = algo if algo in hashlib.algorithms_available else None
            print(f"GET {f['path']} ({human(f['size'])})")
            try:
                got = download(url, dest, args.api_token, algo)
            except Exception as e:  # keep going; report at the end
                print(f"  FAILED: {e}")
                failures.append((f["path"], str(e)))
                continue
            if algo and got != f["checksum"]["value"]:
                mismatches.append(f["path"])
                print(f"  WARNING: {algo} checksum differs from Dataverse's record")
        manifest.append({
            "path": f["path"], "bytes": f["size"], "location": location,
            "checksum": f["checksum"], "dataverse_file_id": f["id"],
            "dataverse_url": f"{args.server}/file.xhtml?fileId={f['id']}",
        })

    with open("metadata/file_manifest.json", "w", encoding="utf-8") as fh:
        json.dump({"doi": bare_doi, "files": manifest}, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    release_files = [f for f in groups["release"] if args.large_dir]
    if release_files:
        with open("metadata/LARGE_FILES_IN_RELEASE.txt", "w") as fh:
            fh.write("# original path\trelease asset name\tbytes\n")
            for f in release_files:
                fh.write(f"{f['path']}\t{f['path'].replace('/', '__')}\t{f['size']}\n")

    skipped = groups["skipped"] + ([] if args.large_dir else groups["release"])
    if skipped:
        with open("metadata/SKIPPED_LARGE_FILES.txt", "w") as fh:
            fh.write(f"# Files not stored on GitHub. Download them from https://doi.org/{bare_doi}\n")
            fh.write("# original path\tbytes\tdataverse file URL\n")
            for f in skipped:
                fh.write(f"{f['path']}\t{f['size']}\t{args.server}/file.xhtml?fileId={f['id']}\n")

    write_citation(meta, version, bare_doi, repo_url)

    print(f"\nDone: {len(groups['repo'])} files in {args.out}/, {len(release_files)} for the release, "
          f"{len(skipped)} logged as skipped. Wrote CITATION.cff, .zenodo.json, metadata/.")
    if mismatches:
        print(f"Checksum warnings on {len(mismatches)} files: {', '.join(mismatches)}")
    if failures:
        print(f"{len(failures)} downloads FAILED:")
        for path, err in failures:
            print(f"  {path}: {err}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
