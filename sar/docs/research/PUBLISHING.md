# Publishing research notes as preprints, with linked data and code

**Registry ID: 2050** · **Status: PROCESS NOTE** · Not legal advice.

How to turn each research note in `sar/docs/research/` into a citable SSRN preprint with a DOI'd
code archive and a DOI'd dataset. Related notes: `INVENTION-DISCLOSURE.md` (**2040**),
`vhr-radar-lidar-fusion.md` (**2030**), `soil-edna-detection.md` (**2000**),
`phone-gpr-addon.md` (**2020**).

> **Read step 0 before anything else.** Posting a preprint is a public disclosure.

---

## 0. STOP — patent filing comes before public posting

`INVENTION-DISCLOSURE.md` (**2040**) says it plainly: *"any public demo, conference talk, or
open-sourcing **before** provisional filing can start clocks / destroy novelty in some
jurisdictions. Keep private until filed."*

- The U.S. allows a 12-month grace period for an inventor's own disclosure; **many jurisdictions
  (EPO, China, and others) have no such general grace period** — a public preprint can bar a
  patent there permanently.
- SSRN posting, a public Zenodo record, a public Dataverse dataset, and flipping this repo public
  are all **public disclosures**. So is a conference talk or a demo video.
- **Order of operations:** file the USPTO provisional (2040 step 3) → note the application number
  and filing date → *then* post. Do not reverse it to "post now, file later" without counsel.
- If a preprint must go out first for priority-of-publication reasons, that is a decision for
  counsel, recorded in 2040, not an engineering decision.

**Gate:** no step below is executed for a given note until 2040 records a provisional filing
receipt (or counsel's written waiver) for the concept that note describes.

---

## 1. Pick the right venue for each artifact

| Artifact | Where | Who may post | DOI? | Cost |
|---|---|---|---|---|
| The paper / note itself | **SSRN** (preprint network) | Anyone; free author account | SSRN gives an abstract ID and permanent URL; DOIs are assigned for some networks/series, not guaranteed for every working paper | Free to post in most networks |
| Code snapshot | **Zenodo**, via the GitHub integration | Anyone, any repo, no institutional affiliation needed | Yes — a concept DOI plus a per-release DOI | Free |
| Data (tabular, rasters, instrument exports) | **Harvard Dataverse** | **Anyone, Harvard or not** | Yes — DOI per dataset and per file | Free up to **1 TB** per non-Harvard account (2.5 TB for Harvard affiliates); fee-based Large Data Services above that |
| Data (if it belongs with the code) | Zenodo, same record as the release | Anyone | Yes | Free (50 GB/record default) |

### What's actually new at Harvard (checked 2026-10-21, America/Denver)

Audrey mentioned "a new Harvard whitepaper repository." There isn't one. What exists:

- **Harvard Dataverse** — <https://dataverse.harvard.edu> · support: <https://support.dataverse.harvard.edu/researchers>.
  Open to **all researchers inside and outside Harvard**. Self-deposit up to **2.5 GB per file**
  through the browser (contact them for larger), **1 TB free per non-Harvard account**, 2.5 TB for
  Harvard affiliates. Every published dataset and datafile gets a **DOI**; contributors can be
  identified by **ORCID** and other IDs. CC0 is strongly encouraged but other terms are allowed.
  **No deposit fee.** Sensitive/identifiable data is **not** accepted — everything must be
  de-identified, and HUIT Security Level 3/4 data is refused. Accounts can be created with
  ORCID, GitHub, or Google as well as HarvardKey. Fee-based Large Data Services exist for
  collections over 2.5 TB and are open to non-Harvard groups at a higher rate.
  **→ This is the one Audrey can actually use, and it is the right home for our data.**
- **DASH** — <https://dash.harvard.edu>. Harvard's central open-access institutional repository
  (70,000+ works: articles, conference proceedings, **working papers**, theses). Deposit is limited
  to **full-time affiliated members of the Harvard research community**. Items get persistent URLs,
  not necessarily DOIs. **Not open to us** without a Harvard affiliation. The "new" part is
  infrastructure, not access: DASH has been migrating to a current DSpace version (with 4Science),
  and Harvard's Digital Repository Service modernization (DRS3) is scheduled for full production
  release in **fall 2026**. No new public-facing submission route for outside authors.
- **Harvard Data Science Review (HDSR)** — <https://hdsr.mitpress.mit.edu>. A peer-reviewed open
  access journal of the Harvard Data Science Initiative, published with MIT Press. Open to anyone,
  **no article processing charges**, CC-BY 4.0, authors retain copyright. But it is **proposal-first**:
  you submit a 1–2 page proposal through Editorial Manager and only write a full manuscript if
  invited; unsolicited full manuscripts are returned unread. Exclusive submissions only, though
  **prior deposit in a repository such as arXiv is explicitly allowed**. Special issues (e.g. the
  "Digital Twins" issue, submissions to 15 July 2026) do take full manuscripts directly.
  **→ A journal, not a whitepaper repository.** Plausible later home for a methods paper; not where
  a working note goes.
- **No new Harvard preprint or working-paper server** for 2025–2026 was found on the official
  sites. If Audrey has a specific page in mind, get the URL and we will re-check.

Non-Harvard alternatives if a topic doesn't fit: **arXiv** (eess.SP / eess.IV for the SAR work;
needs endorsement for a first submission), **bioRxiv**, **OSF Preprints**, **EarthArXiv**.

---

## 2. Per-note workflow

Do these in order for each research note.

### 2.1 Prepare the manuscript
1. Copy the note into a manuscript file; keep the registry ID in the title block.
2. Strip anything case-related: locations, agency names, PII, any live case soil or imagery.
3. Keep the discipline the notes already hold — **cite sources only; claim no detection results**
   that a labelled panel hasn't produced. An unsupported performance claim in a public preprint is
   worse than no preprint.
4. Verify every citation resolves (DOI or publisher page) at the time of posting.
5. Add an explicit "Data and code availability" section — fill in the DOIs from 2.2 and 2.3.

### 2.2 Archive the code with Zenodo's GitHub integration
1. Sign in to <https://zenodo.org> with the GitHub account that owns the repo.
2. **Zenodo → GitHub** settings, flip the repository's switch **On**. Zenodo only sees repos you
   admin, and **only public repos can be enabled**, so this requires the repo (or an extracted
   subset) to be public — which is a disclosure, so re-read step 0.
   - If `forensicfinders` must stay private, publish a **code-only extract** (e.g. just
     `sar/geo_connectors/`) as a separate public repo and archive that.
3. Add `CITATION.cff` (section 3) and a `LICENSE` **before** cutting the release — Zenodo reads
   `CITATION.cff` for authors and title.
4. Cut a GitHub release with a real version tag (`v0.1.0`). Zenodo picks up the tarball and mints a
   **version DOI**, plus a **concept DOI** that always resolves to the newest version.
5. Cite the **concept DOI** in the paper and the **version DOI** in the methods section, so a reader
   can get the exact code the paper used.
6. Paste the Zenodo DOI badge into the repo README.

### 2.3 Deposit the data on Harvard Dataverse
1. Create an account at <https://dataverse.harvard.edu> — you can sign in with **ORCID** or GitHub;
   no Harvard affiliation needed.
2. Create a Dataverse collection for the project, then a dataset per paper.
3. Upload only de-identified, non-sensitive data: synthetic panels, spiked-soil dilution results,
   instrument exports with identifiers stripped, labelled polygons for public ground.
   **Never upload case data.** Dataverse does not accept sensitive data.
4. Fill in metadata, add every author's **ORCID**, choose a license (CC0 is encouraged; pick
   something else deliberately if needed), and link the dataset to the related publication.
5. Publish → you get a dataset **DOI** (and per-file DOIs). Put it in the paper's data-availability
   section, and cite the paper back from the Dataverse record.
6. Keep versions: minor version for metadata, major version for new or replaced files.

### 2.4 Post to SSRN
1. Create a free author account at <https://www.ssrn.com>; connect **ORCID**.
2. Submit the paper to the appropriate network/series, with abstract, keywords, JEL/subject codes,
   and all co-authors listed with their ORCIDs.
3. In the abstract and in the paper, include the Zenodo concept DOI and the Dataverse DOI.
4. Note SSRN's moderation delay; the paper is not public until approved.
5. When SSRN returns the abstract ID / permanent URL, record it in 2040's document-control table
   alongside the provisional application number, with the dates in order.

### 2.5 Close the loop
- Add the SSRN URL to the Zenodo record's "related identifiers" and to the Dataverse dataset's
  publication field, so all three point at each other.
- Update `CITATION.cff` with the preprint DOI and re-release, so later citations resolve.
- Log the posting date in 2040. The disclosure clock starts the day it goes public.

---

## 3. CITATION.cff

A `CITATION.cff` at the repo root tells GitHub, Zenodo, and reference managers how to cite the
software. GitHub renders a "Cite this repository" button from it; Zenodo reads it at release time.

- Template: [`CITATION.cff.template`](./CITATION.cff.template) in this directory. Copy it to the repo
  root as `CITATION.cff`, fill in the `TODO` fields, and validate it (e.g. the `cffconvert` tool or
  <https://citation-file-format.github.io>) before the first release.
- Format reference: <https://citation-file-format.github.io> · schema 1.2.0.
- Keep `version`, `date-released`, and the DOI in `identifiers` in step with each tagged release.

## 4. ORCID — do this first, it is five minutes

Register once at <https://orcid.org/register> (free) and use the same iD everywhere: SSRN, Zenodo,
Harvard Dataverse, GitHub profile, `CITATION.cff`. It is what keeps "A. Evans" on a preprint, a
dataset, and a code archive resolvably the same person, and Dataverse and SSRN both accept it as a
sign-in or contributor identifier. Add co-authors' iDs to every record; do not invent one for
someone else.

---

## 5. Checklist per note

- [ ] 2040 records a provisional filing (or counsel waiver) for this concept — **gate**
- [ ] Manuscript scrubbed of case data and of unsupported performance claims
- [ ] Every citation re-verified
- [ ] ORCID in place for every author
- [ ] `CITATION.cff` added and validated
- [ ] Public code repo/extract + `LICENSE` + GitHub release → Zenodo concept and version DOIs
- [ ] De-identified data published on Harvard Dataverse → dataset DOI
- [ ] Data/code availability section filled in with both DOIs
- [ ] SSRN submission approved; abstract ID recorded
- [ ] Cross-links added in all three places; posting date logged in 2040
