"""
Connection test for Pinecone and Supabase.
Run once to verify setup. Delete after confirmation.
"""
import os
from dotenv import load_dotenv
import structlog

load_dotenv()
logger = structlog.get_logger()


def test_pinecone() -> bool:
    """Test Pinecone connection and index existence."""
    try:
        from pinecone import Pinecone
        
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        indexes = pc.list_indexes()
        index_names = [idx.name for idx in indexes]
        
        target = os.getenv("PINECONE_INDEX_NAME", "rag-knowledge-base")
        
        if target in index_names:
            logger.info("pinecone_connected", index=target, status="OK")
            print(f"[OK] Pinecone connected. Index '{target}' found.")
            return True
        else:
            print(f"[FAIL] Index '{target}' not found. Available: {index_names}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Pinecone error: {e}")
        return False


def test_supabase() -> bool:
    """Test Supabase connection and table existence."""
    try:
        from supabase import create_client
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        client = create_client(url, key)
        
        # Try a simple select on documents table
        result = client.table("documents").select("id").limit(1).execute()
        
        logger.info("supabase_connected", status="OK")
        print("[OK] Supabase connected. 'documents' table accessible.")
        return True
        
    except Exception as e:
        print(f"[FAIL] Supabase error: {e}")
        return False


if __name__ == "__main__":
    print("\n=== Testing Connections ===\n")
    pc_ok = test_pinecone()
    sb_ok = test_supabase()
    
    print("\n=== Results ===")
    print(f"Pinecone:  {'PASS' if pc_ok else 'FAIL'}")
    print(f"Supabase:  {'PASS' if sb_ok else 'FAIL'}")
    
    if pc_ok and sb_ok:
        print("\nAll systems ready. Proceed to Step 3.")
    else:
        print("\nFix failing connections before proceeding.")