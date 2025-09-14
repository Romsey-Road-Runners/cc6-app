#!/usr/bin/env python3
"""
CC6 Firestore Database Restore Script

This script restores a CC6 Firestore database from a backup file,
including all collections and subcollections.
"""

import json
import sys
from google.cloud import firestore

def restore_cc6_firestore(backup_file):
    """Restore CC6 Firestore database from backup file"""
    
    print(f"Starting restore from {backup_file}...")
    
    # Load backup data
    try:
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Backup file '{backup_file}' not found")
        return False
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in backup file '{backup_file}'")
        return False
    
    db = firestore.Client()
    
    # Restore simple collections
    print("Restoring participants...")
    restore_collection(db, "participants", backup_data.get("participants", {}))
    
    print("Restoring clubs...")
    restore_collection(db, "clubs", backup_data.get("clubs", {}))
    
    print("Restoring admin emails...")
    restore_collection(db, "admin_emails", backup_data.get("admin_emails", {}))
    
    # Restore seasons with subcollections
    print("Restoring seasons with races and results...")
    seasons_data = backup_data.get("season", {})
    
    for season_id, season_data in seasons_data.items():
        print(f"  Restoring season: {season_id}")
        
        # Extract races data before storing season
        races_data = season_data.pop("races", {})
        
        # Store season document
        db.collection("season").document(season_id).set(season_data)
        
        # Restore races subcollection
        for race_id, race_data in races_data.items():
            print(f"    Restoring race: {race_id}")
            
            # Extract results data before storing race
            results_data = race_data.pop("results", {})
            
            # Store race document
            db.collection("season").document(season_id).collection("races").document(race_id).set(race_data)
            
            # Restore results subcollection
            if results_data:
                restore_subcollection(
                    db.collection("season").document(season_id).collection("races").document(race_id),
                    "results",
                    results_data
                )
    
    print("Restore completed successfully!")
    
    # Print summary
    print("\nRestore Summary:")
    print(f"  Participants: {len(backup_data.get('participants', {}))}")
    print(f"  Clubs: {len(backup_data.get('clubs', {}))}")
    print(f"  Admin emails: {len(backup_data.get('admin_emails', {}))}")
    print(f"  Seasons: {len(backup_data.get('season', {}))}")
    
    total_races = sum(len(season_data.get('races', {})) for season_data in backup_data.get('season', {}).values())
    total_results = sum(
        len(race_data.get('results', {})) 
        for season_data in backup_data.get('season', {}).values() 
        for race_data in season_data.get('races', {}).values()
    )
    print(f"  Total races: {total_races}")
    print(f"  Total results: {total_results}")
    
    return True

def restore_collection(db, collection_name, documents):
    """Restore a simple collection"""
    batch = db.batch()
    batch_count = 0
    
    for doc_id, doc_data in documents.items():
        doc_ref = db.collection(collection_name).document(doc_id)
        batch.set(doc_ref, doc_data)
        batch_count += 1
        
        # Firestore batch limit is 500 operations
        if batch_count >= 500:
            batch.commit()
            batch = db.batch()
            batch_count = 0
    
    # Commit remaining operations
    if batch_count > 0:
        batch.commit()

def restore_subcollection(parent_doc_ref, subcollection_name, documents):
    """Restore a subcollection"""
    db = parent_doc_ref._client
    batch = db.batch()
    batch_count = 0
    
    for doc_id, doc_data in documents.items():
        doc_ref = parent_doc_ref.collection(subcollection_name).document(doc_id)
        batch.set(doc_ref, doc_data)
        batch_count += 1
        
        # Firestore batch limit is 500 operations
        if batch_count >= 500:
            batch.commit()
            batch = db.batch()
            batch_count = 0
    
    # Commit remaining operations
    if batch_count > 0:
        batch.commit()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python restore.py <backup_file.json>")
        sys.exit(1)
    
    backup_file = sys.argv[1]
    
    # Confirm before proceeding
    response = input(f"This will overwrite existing data in Firestore. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Restore cancelled.")
        sys.exit(0)
    
    success = restore_cc6_firestore(backup_file)
    sys.exit(0 if success else 1)