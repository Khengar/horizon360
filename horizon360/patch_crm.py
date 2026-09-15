import re

with open("frontend/src/pages/CRMCoreListView.tsx", "r") as f:
    content = f.read()

# Fix customers create/update
old_customers = """      createFn: (data) => horizonApi.createCustomer(data),
      updateFn: (id, data) => horizonApi.updateCustomer(id as string, data),"""
new_customers = """      createFn: (data) => {
        const payload = {
          primary_email: data.primary_email,
          primary_phone: data.primary_phone,
          attributes: {
            firstName: data.first_name,
            lastName: data.last_name,
            company: data.company,
            status: data.status
          }
        };
        return horizonApi.createCustomer(payload);
      },
      updateFn: (id, data) => {
        const payload = {
          primary_email: data.primary_email,
          primary_phone: data.primary_phone,
          attributes: {
            firstName: data.first_name,
            lastName: data.last_name,
            company: data.company,
            status: data.status
          }
        };
        return horizonApi.updateCustomer(id as string, payload);
      },"""

content = content.replace(old_customers, new_customers)

with open("frontend/src/pages/CRMCoreListView.tsx", "w") as f:
    f.write(content)
