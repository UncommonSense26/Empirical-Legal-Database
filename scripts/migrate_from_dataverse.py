#!/usr/bin/env python3
"""Copy a published Harvard Dataverse dataset into this repository.

Downloads every file in the latest published version of the dataset, saves
the full Dataverse metadata, and generates CITATION.cff and .zenodo.json so
GitHub shows a "Cite this repository" button and any Zenodo DOI minted from
a GitHub release is linked back to the original Dataverse DOI.

Usage:
    python scripts/migrate_from_dataverse.py doi:10.7910/DVN/XXXXXX
    python scripts/migrate_from_dataverse.py 10.7910/DVN/XXXXXX --api-token TOKEN  # restricted files
    python scripts/migrate_from_dataverse.py doi:10.7910/DVN/XXXXXX --list        # show files and sizes only
    python scripts/migrate_from_dataverse.py doi:... --large-dir large_files      # keep >100 MB files aside

Standard library only (Python 3.8+).
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request

SERVER = "https://dataverse.harvard.edu"
GITHUB_FILE_LIMIT = 100 * 1024 * 1024  # GitHub rejects files > 100 MB without LFS
RELEASE_ASSET_LIMIT = 2 * 1024 * 1024 * 1024  # GitHub release assets max out at 2 GB


def get_json(url, token=None):
    req = urllib.request.Request(url)
    if token:
        req.add_header("X-Dataverse-key", token)
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def download(url, dest, token=None):
    req = urllib.request.Request(url)
    if token:
        req.add_header("X-Dataverse-key", token)
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    with urllib.request.urlopen(req) as resp, open(dest, "wb") as out:
        while chunk := resp.read(1 << 20):
            out.write(chunk)


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("doi", help="e.g. doi:10.7910/DVN/XXXXXX")
    ap.add_argument("--server", default=SERVER)
    ap.add_argument("--api-token", default=os.environ.get("DATAVERSE_API_TOKEN"))
    ap.add_argument("--out", default="data", help="directory for the data files")
    ap.add_argument("--large-dir", help="download files over 100 MB here (for a GitHub release) "
                                        "instead of skipping them")
    ap.add_argument("--list", action="store_true", help="print files and sizes, download nothing")
    args = ap.parse_args()

    doi = args.doi.strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    if not doi.startswith("doi:"):
        doi = "doi:" + doi
    bare_doi = doi[4:]

    pid = urllib.parse.quote(doi, safe="")
    meta = get_json(f"{args.server}/api/datasets/:persistentId/?persistentId={pid}", args.api_token)["data"]
    version = meta["latestVersion"]

    if args.list:
        files = version.get("files", [])
        total = 0
        for entry in files:
            df = entry["dataFile"]
            name = df.get("originalFileName") or df["filename"]
            size = df.get("originalFileSize") or df.get("filesize") or 0
            total += size
            flag = " (over 100 MB)" if size > GITHUB_FILE_LIMIT else ""
            print(f"{size / 1e6:10.1f} MB  {os.path.join(entry.get('directoryLabel') or '', name)}{flag}")
        print(f"{total / 1e6:10.1f} MB  total, {len(files)} files")
        return 0

    os.makedirs("metadata", exist_ok=True)
    with open("metadata/dataverse_metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    skipped = []
    large = []
    for entry in version.get("files", []):
        df = entry["dataFile"]
        name = df.get("originalFileName") or df["filename"]
        rel = os.path.join(entry.get("directoryLabel") or "", name)
        dest = os.path.join(args.out, rel)
        size = df.get("originalFileSize") or df.get("filesize") or 0
        if size > GITHUB_FILE_LIMIT:
            if args.large_dir and size <= RELEASE_ASSET_LIMIT:
                # release assets are flat, so encode the folder into the file name
                dest = os.path.join(args.large_dir, rel.replace(os.sep, "__"))
                large.append((rel, os.path.basename(dest), size))
            else:
                skipped.append((rel, size))
                print(f"SKIP (too large for GitHub): {rel}")
                continue
        # format=original returns the uploaded file rather than Dataverse's .tab conversion
        url = f"{args.server}/api/access/datafile/{df['id']}"
        if df.get("originalFileName"):
            url += "?format=original"
        print(f"GET {rel} ({size} bytes)")
        download(url, dest, args.api_token)

    if skipped:
        with open("metadata/SKIPPED_LARGE_FILES.txt", "w") as f:
            for rel, size in skipped:
                f.write(f"{rel}\t{size}\n")

    if large:
        with open("metadata/LARGE_FILES_IN_RELEASE.txt", "w") as f:
            f.write("# original path\trelease asset name\tbytes\n")
            for rel, asset, size in large:
                f.write(f"{rel}\t{asset}\t{size}\n")

    cit = version["metadataBlocks"]["citation"]
    title = field(cit, "title") or "Empirical Legal Database"
    authors = [a["authorName"]["value"] for a in field(cit, "author") or []]
    desc = " ".join(d["dsDescriptionValue"]["value"] for d in field(cit, "dsDescription") or [])
    desc = re.sub(r"<[^>]+>", "", desc).strip()
    keywords = [k["keywordValue"]["value"] for k in field(cit, "keyword") or [] if "keywordValue" in k]
    license_name = (version.get("license") or {}).get("name", "")
    released = (version.get("releaseTime") or meta.get("publicationDate") or "")[:10]

    lines = [
        "cff-version: 1.2.0",
        'message: "If you use this dataset, please cite it using the metadata below."',
        "type: dataset",
        f"title: {yaml_str(title)}",
        "authors:",
    ]
    for a in authors or ["Unknown"]:
        last, first = split_name(a)
        lines.append(f"  - family-names: {yaml_str(last)}")
        if first:
            lines.append(f"    given-names: {yaml_str(first)}")
    lines += [
        f"doi: {bare_doi}",
        "identifiers:",
        "  - type: doi",
        f"    value: {bare_doi}",
        '    description: "Original Harvard Dataverse DOI"',
        f"url: {yaml_str('https://doi.org/' + bare_doi)}",
    ]
    if released:
        lines.append(f"date-released: {released}")
    if license_name.startswith("CC0"):
        lines.append("license: CC0-1.0")
    elif license_name.startswith("CC BY"):
        lines.append("license: CC-BY-4.0")
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
        "creators": [{"name": a} for a in authors],
        "description": desc or title,
        "keywords": keywords,
        "related_identifiers": [
            {"identifier": bare_doi, "relation": "isNewVersionOf", "scheme": "doi"}
        ],
    }
    if license_name.startswith("CC0"):
        zenodo["license"] = "cc-zero"
    elif license_name.startswith("CC BY"):
        zenodo["license"] = "cc-by-4.0"
    with open(".zenodo.json", "w", encoding="utf-8") as f:
        json.dump(zenodo, f, indent=2, ensure_ascii=False)
        f.write("\n")

    n = len(version.get("files", []))
    print(f"\nDone. {n - len(skipped) - len(large)} files in ./{args.out}, "
          f"{len(large)} large files in ./{args.large_dir}, {len(skipped)} skipped. "
          f"Wrote CITATION.cff, .zenodo.json, metadata/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
