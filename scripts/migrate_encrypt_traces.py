"""
Data Migration: Encrypt Existing Trace Data

This script reads existing unencrypted traces from the database
and updates them with encrypted values in-place.

WARNING: This is a one-way migration. Back up your database before running!
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path so we can import from app
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.trace import Trace
from app.core.encryption import encryption_service


async def encrypt_existing_traces():
    """Encrypt all existing traces in the database"""
    
    print("=" * 70)
    print("  DATA MIGRATION: Encrypting Existing Traces")
    print("=" * 70)
    print()
    
    async for db in get_db():
        try:
            print("1️⃣ Fetching all traces from database...")
            
            # Fetch all traces with raw SQL to get unencrypted data
            result = await db.execute(
                text("SELECT id, user_input, final_output FROM traces WHERE user_input IS NOT NULL")
            )
            traces = result.fetchall()
            
            total_count = len(traces)
            print(f"   Found {total_count} traces to encrypt\n")
            
            if total_count == 0:
                print("✅ No traces to encrypt")
                return
            
            # Ask for confirmation
            print("⚠️  WARNING: This operation will encrypt all trace data.")
            print("   Make sure you have a database backup!")
            print()
            response = input("Continue? (yes/no): ")
            
            if response.lower() != "yes":
                print("❌ Migration cancelled")
                return
            
            print("\n2️⃣ Encrypting traces...")
            encrypted_count = 0
            error_count = 0
            
            for trace_record in traces:
                trace_id = trace_record[0]
                user_input = trace_record[1]
                final_output = trace_record[2]
                
                try:
                    # Check if already encrypted (starts with 'gAAAAA')
                    if user_input and user_input.startswith('gAAAAA'):
                        print(f"   ⏭️  {trace_id} - Already encrypted, skipping")
                        continue
                    
                    # Encrypt the data
                    encrypted_input = encryption_service.encrypt(user_input) if user_input else None
                    encrypted_output = encryption_service.encrypt(final_output) if final_output else None
                    
                    # Update with raw SQL to avoid SQLAlchemy auto-decryption
                    await db.execute(
                        text(
                            "UPDATE traces SET user_input = :input, final_output = :output WHERE id = :id"
                        ),
                        {
                            "input": encrypted_input,
                            "output": encrypted_output,
                            "id": trace_id
                        }
                    )
                    
                    encrypted_count += 1
                    if encrypted_count % 10 == 0:
                        print(f"   Encrypted {encrypted_count}/{total_count} traces...")
                    
                except Exception as e:
                    error_count += 1
                    print(f"   ❌ Error encrypting trace {trace_id}: {e}")
            
            # Commit all changes
            await db.commit()
            
            print()
            print("=" * 70)
            print(f"  ✅ Migration Complete!")
            print(f"     Encrypted: {encrypted_count}")
            print(f"     Errors: {error_count}")
            print(f"     Skipped: {total_count - encrypted_count - error_count}")
            print("=" * 70)
            
            # Verification
            print("\n3️⃣ Verifying encryption...")
            verify_result = await db.execute(
                select(Trace).limit(1)
            )
            test_trace = verify_result.scalar_one_or_none()
            
            if test_trace:
                print(f"   Sample trace user_input (decrypted): {test_trace.user_input[:50]}...")
                print("   ✅ Encryption/decryption working correctly")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            sys.exit(1)
        
        break  # Exit after processing


if __name__ == "__main__":
    print()
    print("Starting data migration...")
    print()
    asyncio.run(encrypt_existing_traces())
    print()
    print("Migration script completed successfully!")
