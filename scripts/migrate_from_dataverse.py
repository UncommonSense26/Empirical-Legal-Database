#!/usr/bin/env python3
"""Copy a published Harvard Dataverse dataset into this repository.

Downloads every file in the latest published version of the dataset, saves
the full Dataverse metadata, and generates CITATION.cff and .zenodo.json so
GitHub shows a "Cite this repository" button and any Zenodo DOI minted from
a GitHub release is linked back to the original Dataverse DOI.

Usage:
    python scripts/migrate_from_dataverse.py doi:10.7910/DVN/XXXXXX
    python scripts/migrate_from_dataverse.py 10.7910/DVN/XXXXXX --api-token TOKEN  # restricted files

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
    args = ap.parse_args()

    doi = args.doi.strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    if not doi.startswith("doi:"):
        doi = "doi:" + doi
    bare_doi = doi[4:]

    pid = urllib.parse.quote(doi, safe="")
    meta = get_json(f"{args.server}/api/datasets/:persistentId/?persistentId={pid}", args.api_token)["data"]
    version = meta["latestVersion"]

    os.makedirs("metadata", exist_ok=True)
    with open("metadata/dataverse_metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    skipped = []
    for entry in version.get("files", []):
        df = entry["dataFile"]
        name = df.get("originalFileName") or df["filename"]
        rel = os.path.join(entry.get("directoryLabel") or "", name)
        dest = os.path.join(args.out, rel)
        size = df.get("originalFileSize") or df.get("filesize") or 0
        if size > GITHUB_FILE_LIMIT:
            skipped.append((rel, size))
            print(f"SKIP (>100 MB, use Git LFS): {rel}")
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

    print(f"\nDone. {len(version.get('files', [])) - len(skipped)} files in ./{args.out}, "
          f"{len(skipped)} skipped. Wrote CITATION.cff, .zenodo.json, metadata/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
