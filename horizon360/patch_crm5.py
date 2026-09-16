import re

with open("frontend/src/pages/CRMCoreListView.tsx", "r") as f:
    content = f.read()

old_deals = """      createFn: (data) => {
        // Just send data; DRF will ignore extra fields. If user typed a customer ID, it could be sent.
        return horizonApi.createDeal(data);
      },
      updateFn: (id, data) => {
        return horizonApi.updateDeal(id, data);
      },"""

new_deals = """      createFn: (data) => {
        const payload = { ...data, lost_reason: data.description };
        return horizonApi.createDeal(payload);
      },
      updateFn: (id, data) => {
        const payload = { ...data, lost_reason: data.description };
        return horizonApi.updateDeal(id, payload);
      },"""
content = content.replace(old_deals, new_deals)

old_deal_init = """        if (entity === 'companies' && record.attributes) {
          if (f.name === 'phone') initData[f.name] = record.attributes.phone || '';
          if (f.name === 'email') initData[f.name] = record.attributes.email || '';
          if (f.name === 'address') initData[f.name] = record.attributes.address || '';
          if (f.name === 'website') initData[f.name] = record.attributes.website || '';
        }"""
new_deal_init = """        if (entity === 'companies' && record.attributes) {
          if (f.name === 'phone') initData[f.name] = record.attributes.phone || '';
          if (f.name === 'email') initData[f.name] = record.attributes.email || '';
          if (f.name === 'address') initData[f.name] = record.attributes.address || '';
          if (f.name === 'website') initData[f.name] = record.attributes.website || '';
        }
        if (entity === 'opportunities') {
          if (f.name === 'description') initData[f.name] = record.lost_reason || '';
        }"""
content = content.replace(old_deal_init, new_deal_init)

with open("frontend/src/pages/CRMCoreListView.tsx", "w") as f:
    f.write(content)
