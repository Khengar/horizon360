import re

with open("frontend/src/pages/CRMCoreListView.tsx", "r") as f:
    content = f.read()

old_code = """        if (entity === 'customers' && record.attributes) {
          if (f.name === 'first_name') initData[f.name] = record.first_name || record.attributes.firstName || '';
          if (f.name === 'last_name') initData[f.name] = record.last_name || record.attributes.lastName || '';
        }"""
new_code = """        if (entity === 'customers' && record.attributes) {
          if (f.name === 'first_name') initData[f.name] = record.first_name || record.attributes.firstName || '';
          if (f.name === 'last_name') initData[f.name] = record.last_name || record.attributes.lastName || '';
          if (f.name === 'company') initData[f.name] = record.attributes.company || '';
          if (f.name === 'status') initData[f.name] = record.attributes.status || '';
        }
        if (entity === 'companies' && record.attributes) {
          if (f.name === 'phone') initData[f.name] = record.attributes.phone || '';
          if (f.name === 'email') initData[f.name] = record.attributes.email || '';
          if (f.name === 'address') initData[f.name] = record.attributes.address || '';
          if (f.name === 'website') initData[f.name] = record.attributes.website || '';
        }"""

content = content.replace(old_code, new_code)

with open("frontend/src/pages/CRMCoreListView.tsx", "w") as f:
    f.write(content)
