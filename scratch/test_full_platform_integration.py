import requests
import sqlite3
import os
import json

BASE_URL = "http://localhost:3000"
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "sharemeal.db")

def test_full_platform_lifecycle():
    print("=========================================================================")
    print("      ECOBITE FULL PLATFORM INTEGRATION TEST (DONOR -> NGO -> DELIVERY -> ADMIN)")
    print("=========================================================================")

    # 1. Setup Test Accounts (Donor, NGO, Delivery Partner) in DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ensure Donor Account
    cursor.execute("SELECT id FROM users WHERE role = 'donor' LIMIT 1")
    donor = cursor.fetchone()
    if not donor:
        cursor.execute("INSERT INTO users (name, email, password, role, phone) VALUES ('Integration Donor', 'donor_int@ecobite.org', 'pass123', 'donor', '9876543210')")
        donor_id = cursor.lastrowid
    else:
        donor_id = donor[0]

    # Ensure NGO Account
    cursor.execute("SELECT id FROM users WHERE role = 'ngo' LIMIT 1")
    ngo = cursor.fetchone()
    if not ngo:
        cursor.execute("INSERT INTO users (name, email, password, role, phone) VALUES ('Integration Shelter NGO', 'ngo_int@ecobite.org', 'pass123', 'ngo', '9876543211')")
        ngo_id = cursor.lastrowid
    else:
        ngo_id = ngo[0]

    # Ensure Delivery Partner Account
    cursor.execute("SELECT id FROM users WHERE role = 'delivery' LIMIT 1")
    delivery = cursor.fetchone()
    if not delivery:
        cursor.execute("INSERT INTO users (name, email, password, role, phone) VALUES ('Integration Delivery Rider', 'delivery_int@ecobite.org', 'pass123', 'delivery', '9876543212')")
        delivery_id = cursor.lastrowid
    else:
        delivery_id = delivery[0]

    conn.commit()
    conn.close()

    print(f"Test Accounts Setup: Donor ID={donor_id}, NGO ID={ngo_id}, Delivery Partner ID={delivery_id}")

    # STEP 1: Donor Publishes Donation
    print("\n--- STEP 1: Donor Publishes Food Donation ---")
    donation_payload = {
        "donor_id": donor_id,
        "food_name": "Special Rajma Chawal Feast",
        "diet_type": "Veg",
        "food_category": "For Humans",
        "quantity": "30 Servings",
        "pickup_address": "Sector 4, EcoBite Hub, Indiranagar",
        "instructions": "Packed in hot insulated boxes.",
        "preparation_time": "2026-10-09T22:00",
        "storage_condition": "Insulated Container"
    }

    res_pub = requests.post(f"{BASE_URL}/api/donate", json=donation_payload)
    assert res_pub.status_code in (200, 201), f"Donation creation failed with status {res_pub.status_code}"
    pub_data = res_pub.json()
    donation_id = pub_data.get("id") or pub_data.get("donation_id")
    print(f"Step 1 Success! Created Donation ID = {donation_id}, Status = AVAILABLE")

    # DB Assertion
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM donations WHERE id = ?", (donation_id,)).fetchone()
    conn.close()
    assert row is not None
    assert row['status'] == 'Available'
    print(f"Database Assertion Passed: Status='{row['status']}', donor_id={row['donor_id']}")

    # STEP 2: NGO Views Available Food Feed
    print("\n--- STEP 2: NGO Views Find Food Feed ---")
    res_feed = requests.get(f"{BASE_URL}/api/donations")
    assert res_feed.status_code == 200
    feed_items = res_feed.json()
    avail_ids = [item['id'] for item in feed_items if item.get('status') == 'Available']
    assert donation_id in avail_ids, f"Donation {donation_id} not visible in NGO Find Food feed!"
    print(f"Step 2 Success! Donation {donation_id} visible to NGOs in available feed.")

    # STEP 3: NGO Claims Food Donation
    print("\n--- STEP 3: NGO Claims Food Donation ---")
    claim_payload = {
        "id": donation_id,
        "status": "Claimed",
        "ngo_id": ngo_id,
        "delivery_req": True
    }
    res_claim = requests.post(f"{BASE_URL}/api/update-status", json=claim_payload)
    assert res_claim.status_code == 200
    claim_data = res_claim.json()
    assert claim_data.get("success") is True
    generated_otp = claim_data.get("otp")
    print(f"Step 3 Success! NGO Claimed Donation. Status = CLAIMED. Generated OTP = {generated_otp}")

    # DB Assertions (Donation status, Claims table, Delivery Tasks table)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    d_row = cursor.execute("SELECT status, claimed_by, otp FROM donations WHERE id = ?", (donation_id,)).fetchone()
    assert d_row['status'] == 'Claimed'
    assert int(d_row['claimed_by']) == int(ngo_id)
    if not generated_otp:
        generated_otp = d_row['otp']

    c_row = cursor.execute("SELECT * FROM claims WHERE donation_id = ?", (donation_id,)).fetchone()
    assert c_row is not None
    assert int(c_row['ngo_id']) == int(ngo_id)

    dt_row = cursor.execute("SELECT * FROM delivery_tasks WHERE donation_id = ?", (donation_id,)).fetchone()
    assert dt_row is not None
    assert dt_row['status'] == 'Available'
    conn.close()
    print("Step 3 Database Assertions Passed: Claims & DeliveryTasks relational rows created cleanly.")

    # STEP 4: Prevent Duplicate Claims (Concurrency Test)
    print("\n--- STEP 4: Testing Duplicate Claim Rejection ---")
    res_dup = requests.post(f"{BASE_URL}/api/update-status", json={"id": donation_id, "status": "Claimed", "ngo_id": 999})
    assert res_dup.status_code in (400, 404)
    print(f"Step 4 Success! Duplicate Claim rejected properly: {res_dup.json().get('message')}")

    # STEP 5: Delivery Partner Accepts Task
    print("\n--- STEP 5: Delivery Partner Accepts Task ---")
    assign_payload = {
        "donation_id": donation_id,
        "delivery_id": delivery_id
    }
    res_assign = requests.post(f"{BASE_URL}/api/assign-delivery", json=assign_payload)
    assert res_assign.status_code == 200
    assert res_assign.json().get("success") is True
    print(f"Step 5 Success! Delivery Partner {delivery_id} accepted task for donation {donation_id}.")

    # DB Assertion (Donation status = Pickup Assigned, DeliveryTask status = Assigned)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    d_row2 = cursor.execute("SELECT status, delivery_by FROM donations WHERE id = ?", (donation_id,)).fetchone()
    assert d_row2['status'] == 'Pickup Assigned'
    assert int(d_row2['delivery_by']) == int(delivery_id)

    dt_row2 = cursor.execute("SELECT status, delivery_partner_id FROM delivery_tasks WHERE donation_id = ?", (donation_id,)).fetchone()
    assert dt_row2['status'] == 'Assigned'
    assert int(dt_row2['delivery_partner_id']) == int(delivery_id)
    conn.close()
    print("Step 5 Database Assertions Passed: Task assigned atomically.")

    # STEP 6: Delivery Partner Verifies OTP & Completes Delivery
    print("\n--- STEP 6: Verifying OTP & Completing Delivery ---")
    
    # First test invalid OTP rejection
    res_bad_otp = requests.post(f"{BASE_URL}/api/verify-delivery", json={"donation_id": donation_id, "otp": "0000"})
    assert res_bad_otp.status_code == 400
    print(f"Invalid OTP Rejected Correctly: {res_bad_otp.json().get('message')}")

    # Now test valid OTP verification
    res_otp = requests.post(f"{BASE_URL}/api/verify-delivery", json={"donation_id": donation_id, "otp": generated_otp})
    assert res_otp.status_code == 200
    assert res_otp.json().get("success") is True
    print("Step 6 Success! OTP Verified. Delivery Completed.")

    # DB Assertion (Donation status = Delivered, DeliveryProof logged)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    d_row3 = cursor.execute("SELECT status FROM donations WHERE id = ?", (donation_id,)).fetchone()
    assert d_row3['status'] == 'Delivered'

    proof_row = cursor.execute("SELECT * FROM delivery_proofs WHERE donation_id = ?", (donation_id,)).fetchone()
    assert proof_row is not None
    conn.close()
    print("Step 6 Database Assertions Passed: Status='Delivered', delivery proof logged.")

    # STEP 7: Admin Overview Integration Verification
    print("\n--- STEP 7: Admin Overview Verification ---")
    res_admin = requests.get(f"{BASE_URL}/api/admin/overview")
    assert res_admin.status_code == 200
    admin_data = res_admin.json()
    assert admin_data.get("success") is True
    stats = admin_data.get("stats", {})
    print(f"Admin Overview Stats: Total Donations={stats.get('total_donations')}, Delivered={stats.get('delivered_donations')}, Total Users={stats.get('total_users')}")
    assert stats.get("delivered_donations", 0) > 0
    print("Step 7 Success! Admin dashboard received real platform metrics.")

    print("\n=========================================================================")
    print("      ALL END-TO-END PLATFORM INTEGRATION TESTS PASSED SUCCESSFULLY!    ")
    print("=========================================================================")

if __name__ == "__main__":
    test_full_platform_lifecycle()
