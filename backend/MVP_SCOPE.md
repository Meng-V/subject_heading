# MVP Scope: AI Subject Heading Assistant

## 🎯 Project Context

This system serves an **East Asian collection in a US academic library**.
Collections may be in Chinese, Japanese, Korean, English, or other languages.

## 📚 Vocabulary Scope

### ✅ MVP Vocabularies (Actively Generated)

| Vocabulary | Description | MARC Indicators | $2 Subfield |
|------------|-------------|-----------------|-------------|
| **LCSH** | Library of Congress Subject Headings | ind2=`0` | None |
| **FAST** | Faceted Application of Subject Terminology | ind2=`7` | `fast` |

### 🔮 Future Extensions (Optional/Display Only)

These vocabularies may appear in imported records but are **not auto-generated** in MVP:

- **GTT** (ind2=7, $2 gtt)
- **RERO** (ind2=7, $2 rero)
- **SWD** (ind2=7, $2 swd)
- **idszbz** (ind2=7, $2 idszbz)
- **ram** (ind2=7, $2 ram)

## 📋 Subject65X JSON Model

The primary data model for subject headings:

```json
{
  "tag": "650",           // 650 (topical), 651 (geographic), 655 (genre/form)
  "ind1": "_",            // First indicator (usually blank)
  "ind2": "0",            // Second indicator: 0=LCSH, 7=other vocabulary
  "vocabulary": "lcsh",   // "lcsh" or "fast" for MVP
  "heading_string": "Calligraphy, Chinese -- Ming-Qing dynasties, 1368-1912",
  "subfields": [
    {"code": "a", "value": "Calligraphy, Chinese"},
    {"code": "y", "value": "Ming-Qing dynasties, 1368-1912"},
    {"code": "0", "value": "http://id.loc.gov/authorities/subjects/sh85018910"}
  ],
  "uri": "http://id.loc.gov/authorities/subjects/sh85018910",
  "authority_id": "sh85018910",
  "source_system": "ai_generated",
  "score": 0.92,
  "explanation": "Primary subject covering Chinese calligraphy during the Ming-Qing period.",
  "status": "suggested"
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `tag` | string | MARC tag: "650", "651", or "655" |
| `ind1` | string | First indicator (usually "_") |
| `ind2` | string | Second indicator: "0" for LCSH, "7" for FAST |
| `vocabulary` | string | "lcsh" or "fast" (MVP) |
| `heading_string` | string | Full heading with subdivisions |
| `subfields` | array | Parsed subfields [{code, value}, ...] |
| `uri` | string | Authority URI (id.loc.gov or FAST) |
| `authority_id` | string | Extracted authority ID (e.g., "sh85018910") |
| `source_system` | string | "ai_generated", "imported", or "manual" |
| `score` | float | Confidence score from vector search (0-1) |
| `explanation` | string | Natural language explanation for cataloger |
| `status` | string | Workflow status (see below) |

### Status Values

| Status | Description |
|--------|-------------|
| `suggested` | AI-generated suggestion |
| `selected` | Librarian selected |
| `rejected` | Librarian rejected |
| `modified` | Librarian modified |
| `imported` | From existing record |

## 🔧 API Response Format

All endpoints return `subjects_65x` array:

```json
{
  "success": true,
  "subjects_65x": [
    { /* Subject65X object */ },
    { /* Subject65X object */ }
  ],
  "message": "Generated 5 Subject65X entries (LCSH/FAST)"
}
```

## 📊 MARC Field Examples

### LCSH Examples

```
650 _0 $a Calligraphy, Chinese $y Ming-Qing dynasties, 1368-1912 $0 http://id.loc.gov/authorities/subjects/sh85018910.
651 _0 $a China $x Civilization $y 960-1644.
655 _0 $a Conference papers and proceedings.
```

### FAST Examples

```
650 _7 $a Calligraphy, Chinese $2 fast $0 (OCoLC)fst00844437.
651 _7 $a China $2 fast $0 (OCoLC)fst01206073.
655 _7 $a Conference papers and proceedings $2 fast $0 (OCoLC)fst01423772.
```

## 🗂️ Subfield Codes

| Code | Description | Example |
|------|-------------|---------|
| `$a` | Main heading | Calligraphy, Chinese |
| `$x` | General subdivision | Technique |
| `$y` | Chronological subdivision | Ming-Qing dynasties, 1368-1912 |
| `$z` | Geographic subdivision | Beijing |
| `$v` | Form subdivision | Congresses |
| `$0` | Authority URI | http://id.loc.gov/... |
| `$2` | Source of heading | fast |

## 🎯 Tag Selection Rules

| Topic Type | MARC Tag | Description |
|------------|----------|-------------|
| `topical` | 650 | Subject matter, themes, concepts |
| `geographic` | 651 | Places, regions, countries |
| `genre` | 655 | Form/genre terms |

## 🔄 Workflow

1. **OCR** → Extract metadata from book images
2. **Topic Generation** → Generate typed topics (topical/geographic/genre)
3. **Authority Match** → Search LCSH and FAST via vector search
4. **Build 65X** → Generate Subject65X objects
5. **Review** → Librarian selects/modifies headings
6. **Submit** → Store final record with selected subjects

## 📁 Data Storage

Records are stored as JSON files:

```
/data/records/{uuid}.json
```

Each record contains:
- Book metadata
- AI-generated topics
- Authority matches
- Final Subject65X selections

## 🚀 API Endpoints

### Core Workflow

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ingest-images` | POST | Multi-image OCR |
| `/api/generate-topics` | POST | Generate typed topics |
| `/api/authority-match` | POST | LCSH/FAST search |
| `/api/build-65x` | POST | Generate Subject65X |
| `/api/submit-final` | POST | Store final record |

### Admin

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/initialize-authorities` | POST | Initialize Weaviate schemas |
| `/api/index-sample-authorities` | POST | Load sample LCSH/FAST data |
| `/api/authority-stats` | GET | Get index statistics |

## 🔒 Design Principles

1. **Vocabulary Field**: Every Subject65X has a `vocabulary` field for future extensibility
2. **MVP Focus**: Only LCSH and FAST are auto-generated
3. **Preserve Imports**: Other vocabularies can be displayed/preserved from imported records
4. **East Asian Support**: Designed for CJK collections in US academic libraries
5. **Cataloger-Friendly**: Natural language explanations for each suggestion

## 📖 References

- [LCSH](https://id.loc.gov/authorities/subjects.html)
- [FAST](https://www.oclc.org/research/areas/data-science/fast.html)
- [MARC 21 Format for Bibliographic Data](https://www.loc.gov/marc/bibliographic/)
