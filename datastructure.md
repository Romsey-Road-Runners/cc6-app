# Firestore Data Model

This document describes the Firestore data model used in this application.

---

## participants (collection)

- **Document ID:** parkrun barcode (string, unique)
- **Fields:**
  - `first_name` (string)
  - `last_name` (string)
  - `date_of_birth` (string, ISO date format, e.g., "1990-01-01")
  - `club` (string, references the club document ID — the club name)
  - `gender` (enum: "M", "F", "Other")

**Example:**
```
{
  "id": "A1234567",
  "first_name": "Jane",
  "last_name": "Doe",
  "date_of_birth": "1990-01-01",
  "club": "Romsey Road Runners",
  "gender": "F"
}
```

---

## clubs (collection)

- **Document ID:** club name (string, unique, normalized)
- **Fields:**
  - `short_names` (array of strings, e.g., `["RRR", "Romsey RR", "Romsey"]`)

**Example:**
```
{
  "id": "Romsey Road Runners",
  "short_names": ["RRR", "Romsey RR", "Romsey"]
}
```

---

## Enumerations

### gender (for participants)
- "M" (Male)
- "F" (Female)
- "Other"

---

## Notes

- The `club` field in the participant document should match the club document's ID (club name).
- If additional club metadata is required in the future (e.g., location, website), add more fields to the club documents.
- For efficient lookups, ensure club names are unique and normalized (e.g., consistent casing and spacing).
- To support club name changes, consider using a unique slug or code as the club document ID instead.
