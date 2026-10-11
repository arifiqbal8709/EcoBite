import urllib.request
import json

BASE_URL = "http://127.0.0.1:3000"

def test_complaint_system():
    print("==================================================")
    print("  ECOBITE CENTRALIZED COMPLAINT SYSTEM TEST SUITE  ")
    print("==================================================")

    # 1. Test Donor Complaint Submission
    donor_payload = json.dumps({
        "full_name": "Test Donor Hero",
        "email": "donor@test.org",
        "user_role": "Donor",
        "phone": "+1987654321",
        "category": "Food Donation Problem",
        "subject": "Donation Not Showing in Listings",
        "description": "My donation of 20 surplus rice meals is not visible to NGOs.",
        "related_donation_id": 1,
        "user_id": 1
    }).encode('utf-8')

    req = urllib.request.Request(
        f"{BASE_URL}/api/complaints/submit",
        data=donor_payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        res_donor = json.loads(resp.read().decode('utf-8'))
        print("[SUCCESS] Donor Complaint Submission:", res_donor)
        assert res_donor['success'] == True
        cmp1_id = res_donor['complaint_id']
        cmp1_ticket = res_donor['ticket_number']

    # 2. Test NGO Complaint Submission (Food Safety Complaint -> Should calculate CRITICAL priority)
    ngo_payload = json.dumps({
        "full_name": "WeCare NGO Partner",
        "email": "ngo@wecare.org",
        "user_role": "NGO",
        "phone": "+1800555123",
        "category": "Food Safety Complaint",
        "subject": "Packaging damage & temperature issue",
        "description": "Donated items arrived unsealed and warm.",
        "related_donation_id": 2,
        "user_id": 2
    }).encode('utf-8')

    req = urllib.request.Request(
        f"{BASE_URL}/api/complaints/submit",
        data=ngo_payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        res_ngo = json.loads(resp.read().decode('utf-8'))
        print("[SUCCESS] NGO Safety Complaint (Critical Priority):", res_ngo)
        assert res_ngo['success'] == True
        assert res_ngo['priority'] == 'CRITICAL'
        cmp2_id = res_ngo['complaint_id']

    # 3. Test Delivery Partner Complaint (OTP Verification Problem)
    del_payload = json.dumps({
        "full_name": "Rapid Rider",
        "email": "driver@ecobite.org",
        "user_role": "Delivery Partner",
        "phone": "+1999888777",
        "category": "OTP Verification Problem",
        "subject": "OTP Code Not Receiving on Recipient Phone",
        "description": "Unable to complete delivery handover because recipient did not receive OTP code.",
        "related_delivery_id": 5,
        "user_id": 3
    }).encode('utf-8')

    req = urllib.request.Request(
        f"{BASE_URL}/api/complaints/submit",
        data=del_payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        res_del = json.loads(resp.read().decode('utf-8'))
        print("[SUCCESS] Delivery Partner Complaint:", res_del)
        assert res_del['success'] == True
        cmp3_id = res_del['complaint_id']

    # 4. Test Admin Listing & Real Statistics Calculation
    req = urllib.request.Request(f"{BASE_URL}/api/admin/complaints")
    with urllib.request.urlopen(req) as resp:
        res_admin = json.loads(resp.read().decode('utf-8'))
        print("[SUCCESS] Admin Complaints Center Real DB Stats:", res_admin['stats'])
        assert res_admin['stats']['total'] >= 3
        assert res_admin['stats']['critical'] >= 1
        assert res_admin['stats']['new'] >= 3

    # 5. Test Admin Reply & Status Update (Set status to WAITING_FOR_USER)
    admin_update_payload = json.dumps({
        "status": "WAITING_FOR_USER",
        "priority": "HIGH",
        "notes": "Requested donor to provide screenshot of the donation error screen."
    }).encode('utf-8')

    req = urllib.request.Request(
        f"{BASE_URL}/api/admin/complaints/{cmp1_id}/update-status",
        data=admin_update_payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        res_stat_update = json.loads(resp.read().decode('utf-8'))
        print("[SUCCESS] Admin Status Update:", res_stat_update)
        assert res_stat_update['success'] == True
        assert res_stat_update['status'] == 'WAITING_FOR_USER'

    # Admin sends public reply
    reply_payload = json.dumps({
        "sender_id": 1,
        "sender_role": "Admin",
        "sender_name": "System Admin",
        "message": "We are investigating your issue. Could you confirm if your donation appears under Scheduled tab?"
    }).encode('utf-8')

    req = urllib.request.Request(
        f"{BASE_URL}/api/complaints/{cmp1_id}/reply",
        data=reply_payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        res_reply = json.loads(resp.read().decode('utf-8'))
        print("[SUCCESS] Admin Reply:", res_reply)
        assert res_reply['success'] == True

    # 6. Test User Reply (Should auto-update status from WAITING_FOR_USER to IN_PROGRESS)
    user_reply_payload = json.dumps({
        "sender_id": 1,
        "sender_role": "Donor",
        "sender_name": "Test Donor Hero",
        "message": "Yes, it shows under Scheduled tab now, thank you!"
    }).encode('utf-8')

    req = urllib.request.Request(
        f"{BASE_URL}/api/complaints/{cmp1_id}/reply",
        data=user_reply_payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        res_user_reply = json.loads(resp.read().decode('utf-8'))
        print("[SUCCESS] User Reply (Auto Status Transition to IN_PROGRESS):", res_user_reply)
        assert res_user_reply['success'] == True
        assert res_user_reply['new_status'] == 'IN_PROGRESS'

    # 7. Test Resolution Workflow (Admin Marks RESOLVED)
    resolve_payload = json.dumps({
        "status": "RESOLVED",
        "notes": "Issue confirmed resolved by donor."
    }).encode('utf-8')

    req = urllib.request.Request(
        f"{BASE_URL}/api/admin/complaints/{cmp1_id}/update-status",
        data=resolve_payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        res_resolve = json.loads(resp.read().decode('utf-8'))
        print("[SUCCESS] Ticket Resolution:", res_resolve)
        assert res_resolve['success'] == True
        assert res_resolve['status'] == 'RESOLVED'

    # 8. Test Ticket Reopening Workflow (User reopens ticket)
    reopen_payload = json.dumps({
        "reason": "Wait, the donation status changed back to draft. Reopening for review."
    }).encode('utf-8')

    req = urllib.request.Request(
        f"{BASE_URL}/api/complaints/{cmp1_id}/reopen",
        data=reopen_payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        res_reopen = json.loads(resp.read().decode('utf-8'))
        print("[SUCCESS] Ticket Reopening:", res_reopen)
        assert res_reopen['success'] == True
        assert res_reopen['status'] == 'REOPENED'

    # 9. Test CSV Export API
    req = urllib.request.Request(f"{BASE_URL}/api/admin/complaints/export")
    with urllib.request.urlopen(req) as resp:
        csv_text = resp.read().decode('utf-8')
        print("[SUCCESS] CSV Export Output Sample:")
        print(csv_text[:200])
        assert "Ticket Number" in csv_text
        assert cmp1_ticket in csv_text

    print("\nALL 8 WORKFLOW & SECURITY INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_complaint_system()
