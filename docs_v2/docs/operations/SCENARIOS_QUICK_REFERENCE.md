# Quick Reference: Operational Scenarios by Priority

**Purpose:** Quick lookup guide for handling common situations by urgency level

---

## 🚨 **URGENT - Handle Immediately (< 15 minutes)**

### Guest Currently Affected
1. **Guest locked out** → Get door code → Update HCP notes → Text cleaner
2. **Guest arrived during cleaning** → Contact cleaner → Prioritize essentials → Manage expectations  
3. **No cleaner showed up** → Call assigned → Find replacement → Update schedule
4. **Property emergency (flood/fire)** → Safety first → Move guest → Cancel cleaning
5. **Guest refuses to leave** → Contact property manager → Document → May need authorities

### Same-Day Service Impact
6. **Same-day turnover behind schedule** → Check progress → Alert next guest → Assign helper
7. **Wrong property being cleaned** → Stop immediately → Redirect → Update correct job
8. **Access code not working** → Contact property manager → Get backup access → Update notes

---

## ⚠️ **HIGH PRIORITY - Handle Within 1 Hour**

### Schedule/Quality Issues  
9. **Major cleanliness complaint** → Schedule re-clean today → Different cleaner → Document issue
10. **Damage discovered** → Photo evidence → Create maintenance job → Notify owner
11. **Late checkout request** → Update Custom Service Time → Reschedule → Check same-day impact
12. **Supplies depleted** → Emergency supply run → Charge to property → Update inventory

### Staff Issues
13. **Cleaner injury** → Ensure safety → Get coverage → File incident report → Workers comp
14. **Multiple cleaner no-shows** → Call backup list → May need to prioritize properties
15. **Vehicle breakdown** → Arrange transport → Reassign routes → Update arrival times

---

## 📋 **MODERATE - Handle Within 2-4 Hours**

### Coordination Required
16. **Special instructions added** → Update HCP if not created → Add to job notes → Alert cleaner
17. **Schedule conflict discovered** → Review assignments → Optimize routes → Reassign as needed
18. **Quality check failed** → Schedule re-inspection → Training note → Follow-up required
19. **Wrong service level billed** → Review line items → Adjust pricing → Issue credit/charge

### System/Process Issues
20. **Webhook not updating** → Check logs → Restart service → Manual sync if needed
21. **Duplicate jobs found** → Keep newest → Cancel extras → Verify single charge
22. **Missing HCP IDs** → Create customer → Add address → Update Properties table

---

## 📅 **ROUTINE - Handle Same Day**

### Administrative Tasks
23. **New property setup** → Create HCP records → Link in Airtable → Test job creation
24. **Bulk schedule changes** → Filter affected → Update systematically → Confirm with staff
25. **Lost item found** → Secure item → Photo document → Contact guest → Arrange return
26. **Reservation modified** → System auto-detects → Verify sync status → Adjust if needed

### Planning/Training
27. **New cleaner first solo** → Assign easy property → Extra time buffer → Follow-up check
28. **Weekly schedule review** → Check workload balance → Identify conflicts → Adjust assignments
29. **Performance issues** → Document specifics → Schedule retraining → Monitor improvement
30. **Month-end reporting** → Completion rates → Quality scores → Revenue tracking

---

## 🎯 **Decision Trees for Common Issues**

### "Job Won't Create"
```
Missing Property HCP IDs? → YES → Create in HCP first
                         ↓ NO
Missing Service Time? → YES → Set Final Service Time  
                      ↓ NO
Invalid Time Format? → YES → Use YYYY-MM-DD HH:MM AM/PM
                     ↓ NO
Check API logs for error
```

### "Cleaner Can't Complete"
```
Access Issue? → YES → Get code/key → Update notes
             ↓ NO
Safety Issue? → YES → Stop work → Document → Reschedule
             ↓ NO  
Time Issue? → YES → Can extend? → Notify next guest
           ↓ NO                 ↓ NO → Assign helper
Continue monitoring
```

### "Guest Complaint"
```
Cleanliness? → YES → Major? → YES → Re-clean today
            ↓ NO           ↓ NO → Note for next time
                      
Damage? → YES → Document → Maintenance needed? → Create job
       ↓ NO                                  ↓ NO → Note only
       
Missing Items? → YES → Check previous guest → Lost & found process
              ↓ NO → Verify with cleaner
```

---

## 📞 **Escalation Guide**

### When to Escalate Immediately:
- Guest safety issue
- Property damage > $500
- Legal situations (police involved)
- System-wide outages
- Multiple property access issues

### Who to Contact:
1. **Property Manager**: Access, maintenance, guest issues
2. **Operations Manager**: Staff, quality, scheduling
3. **System Admin**: Technical, API, webhook issues
4. **Owner/C-Level**: Legal, major incidents, PR issues

---

## ⏱️ **Time Standards**

| Action | Target Time |
|--------|------------|
| Respond to urgent issue | < 15 min |
| Update schedule change | < 30 min |
| Find replacement cleaner | < 45 min |
| Resolve access issue | < 20 min |
| Process lost & found | < 24 hrs |
| Complete re-clean | < 4 hrs |
| Update job after change | < 10 min |

---

## 🔍 **Quick Lookups**

### Common Airtable Filters:
```
// Today's incompletes
AND({Service Date} = TODAY(), {Job Status} != "Completed")

// Sync issues  
OR({Sync Status} = "Wrong Date", {Sync Status} = "Wrong Time")

// Same-day rush
AND({Same-day Turnover} = TRUE, {Service Date} = TODAY())

// Missing jobs
AND({Final Service Time} != "", {Service Job ID} = "")
```

### Useful Commands:
```bash
# Check webhook status
sudo systemctl status webhook

# View recent webhook activity  
tail -f /home/opc/automation/src/automation/logs/webhook.log

# Restart API server
sudo systemctl restart airscripts-api

# Find specific job in logs
grep "job_[id]" /home/opc/automation/src/automation/logs/*.log
```

---

*Quick reference for operational scenarios. For detailed steps, see OPERATIONAL_SCENARIOS.md*