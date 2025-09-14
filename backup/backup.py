#!/usr/bin/env python3
"""
CC6 Firestore Database Backup Script

This script creates a complete backup of the CC6 Firestore database,
including all collections and subcollections.
"""

import json
import os
from datetime import datetime
from google.cloud import firestore

def backup_cc6_firestore(output_file=None):
    """Create a complete backup of the CC6 Firestore database"""
    
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"cc6_backup_{timestamp}.json"
    
    print(f"Starting backup to {output_file}...")
    
    db = firestore.Client()
    backup = {
        "backup_timestamp": datetime.now().isoformat(),
        "participants": {},
        "clubs": {},
        "admin_emails": {},
        "season": {}
    }
    
    # Backup simple collections
    print("Backing up participants...")
    docs = db.collection("participants").stream()
    for doc in docs:
        backup["participants"][doc.id] = doc.to_dict()
    
    print("Backing up clubs...")
    docs = db.collection("clubs").stream()
    for doc in docs:
        backup["clubs"][doc.id] = doc.to_dict()
    
    print("Backing up admin emails...")
    docs = db.collection("admin_emails").stream()
    for doc in docs:
        backup["admin_emails"][doc.id] = doc.to_dict()
    
    # Backup seasons with subcollections
    print("Backing up seasons with races and results...")
    seasons = db.collection("season").stream()
    for season in seasons:
        print(f"  Processing season: {season.id}")
        season_data = season.to_dict()
        season_data["races"] = {}
        
        # Get races subcollection
        races = season.reference.collection("races").stream()
        for race in races:
            print(f"    Processing race: {race.id}")
            race_data = race.to_dict()
            race_data["results"] = {}
            
            # Get results subcollection
            results = race.reference.collection("results").stream()
            for result in results:
                race_data["results"][result.id] = result.to_dict()
            
            season_data["races"][race.id] = race_data
        
        backup["season"][season.id] = season_data
    
    # Save backup to file
    with open(output_file, 'w') as f:
        json.dump(backup, f, indent=2, default=str)
    
    print(f"Backup completed successfully: {output_file}")
    
    # Print summary
    print("\nBackup Summary:")
    print(f"  Participants: {len(backup['participants'])}")
    print(f"  Clubs: {len(backup['clubs'])}")
    print(f"  Admin emails: {len(backup['admin_emails'])}")
    print(f"  Seasons: {len(backup['season'])}")
    
    total_races = sum(len(season_data['races']) for season_data in backup['season'].values())
    total_results = sum(
        len(race_data['results']) 
        for season_data in backup['season'].values() 
        for race_data in season_data['races'].values()
    )
    print(f"  Total races: {total_races}")
    print(f"  Total results: {total_results}")

if __name__ == "__main__":
    import sys
    
    output_file = sys.argv[1] if len(sys.argv) > 1 else None
    backup_cc6_firestore(output_file)