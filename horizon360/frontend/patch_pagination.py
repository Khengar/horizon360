import os
import glob

def patch_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Generic fix for paginated state arrays
    content = content.replace("setCampaigns(campData);", "setCampaigns(Array.isArray(campData) ? campData : (campData?.results || []));")
    content = content.replace("setLeads(leadData);", "setLeads(Array.isArray(leadData) ? leadData : (leadData?.results || []));")
    content = content.replace("setEmployees(empData);", "setEmployees(Array.isArray(empData) ? empData : (empData?.results || []));")
    content = content.replace("setLeaveRequests(leaveData);", "setLeaveRequests(Array.isArray(leaveData) ? leaveData : (leaveData?.results || []));")
    content = content.replace("setDepartments(deptData);", "setDepartments(Array.isArray(deptData) ? deptData : (deptData?.results || []));")

    with open(filepath, 'w') as f:
        f.write(content)

for filepath in glob.glob("src/pages/*.tsx"):
    patch_file(filepath)

