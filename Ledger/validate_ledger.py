import hashlib
import os

LEDGER_FILE = "compliance_ledger.csv"

def validate():
    print("Checking Ledger Integrity...")
    if not os.path.exists(LEDGER_FILE):
        print("No ledger found.")
        return

    with open(LEDGER_FILE, "r") as f:
        lines = f.readlines()[1:] # Skip header
        expected_prev_hash = "0" * 64
        
        for i, line in enumerate(lines):
            parts = line.strip().split(",")
            # Reconstruct the data string exactly as it was logged
            data_content = f"{parts[0]}|{parts[1]}|{parts[2]}|{parts[3]}|{parts[4]}"
            stored_prev_hash = parts[5]
            stored_curr_hash = parts[6]
            
            # Verify link to previous block
            if stored_prev_hash != expected_prev_hash:
                print(f"❌ TAMPERING DETECTED at Line {i+1}! Chain is broken.")
                return

            # Verify current hash
            calculated_hash = hashlib.sha256((stored_prev_hash + data_content).encode()).hexdigest()
            if calculated_hash != stored_curr_hash:
                print(f"❌ DATA CORRUPTION at Line {i+1}! Hash mismatch.")
                return
            
            expected_prev_hash = stored_curr_hash
            
    print("✅ LEDGER VALID: All hashes match. Data is authentic.")

if __name__ == "__main__":
    validate()
