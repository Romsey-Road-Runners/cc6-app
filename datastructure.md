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
  - `gender` (enum: "M", "F")

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

## season (collection)

- **Document ID:** season name (e.g., "2024-25")
- **Subcollections:** `races`

### races (subcollection of season)

- **Document ID:** race name (e.g., "Race 1")
- **Fields:**
  - `date`: string (ISO format, e.g., "2024-10-15")
  - `organising_clubs`: array of club names (strings; matches club document IDs in the clubs collection)

- **Subcollections:** `results`

#### results (subcollection of race)

- **Document ID:** finish token (string)
- **Fields:**
  - `participant`: object (see below)

##### participant (object embedded in result)

- `parkrun_barcode_id`: string
- `first_name`: string
- `last_name`: string
- `gender`: enum ("M", "F")
- `age_category`: string (e.g., "M40-44")
- `club`: string (club name at time of race)

**Example:**
```json
// Document ID: "25"
{
  "participant": {
    "parkrun_barcode_id": "A1234567",
    "first_name": "Jane",
    "last_name": "Doe",
    "gender": "F",
    "age_category": "F40-44",
    "club": "Romsey Road Runners"
  }
}
```

---

## Enumerations

### gender (for participants)
- "M" (Male)
- "F" (Female)

---

### Indexing

A collection group index should be created on `results.participant.club` and `results.participant.parkrun_barcode_id` for efficient queries across all race results.

**A composite index should be created on each race's `results` subcollection for the fields `participant.gender` and `participant.age_category` (for queries like: all F 40-44 finishers in a race).**

---

**Notes:**  
- Embedding participant data in results ensures race data is "frozen in time" and not affected by later participant profile changes.
- `organising_clubs` is an array of club names, matching the club document IDs in the `clubs` collection.
- The `club` field in the participant document should match the club document's ID (club name).
- If additional club metadata is required in the future (e.g., location, website), add more fields to the club documents.
- For efficient lookups, ensure club names are unique and normalized (e.g., consistent casing and spacing).
- To support club name changes, consider using a unique slug or code as the club document ID instead.