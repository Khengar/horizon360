import re

with open("frontend/src/pages/CRMCoreListView.tsx", "r") as f:
    content = f.read()

# Fix companies (accounts) payload
old_companies = """      createFn: (data) => horizonApi.createCompany(data),
      updateFn: (id, data) => horizonApi.updateCompany(id as string, data),"""
new_companies = """      createFn: (data) => {
        const payload = {
          name: data.name,
          domain: data.domain,
          industry: data.industry,
          tier: data.tier,
          attributes: {
            phone: data.phone,
            email: data.email,
            address: data.address,
            website: data.website
          }
        };
        return horizonApi.createCompany(payload);
      },
      updateFn: (id, data) => {
        const payload = {
          name: data.name,
          domain: data.domain,
          industry: data.industry,
          tier: data.tier,
          attributes: {
            phone: data.phone,
            email: data.email,
            address: data.address,
            website: data.website
          }
        };
        return horizonApi.updateCompany(id as string, payload);
      },"""

content = content.replace(old_companies, new_companies)

# Fix products is_active mapping
old_products = """      createFn: (data) => horizonApi.createProduct(data),
      updateFn: (id, data) => horizonApi.updateProduct(id, data),"""
new_products = """      createFn: (data) => {
        const payload = { ...data, is_active: data.is_active === 'Active' || data.is_active === 'true' || data.is_active === true };
        return horizonApi.createProduct(payload);
      },
      updateFn: (id, data) => {
        const payload = { ...data, is_active: data.is_active === 'Active' || data.is_active === 'true' || data.is_active === true };
        return horizonApi.updateProduct(id, payload);
      },"""

content = content.replace(old_products, new_products)

# Fix deals payload (Company/Customer) mapping
old_deals = """      createFn: (data) => horizonApi.createDeal(data),
      updateFn: (id, data) => horizonApi.updateDeal(id, data),"""
new_deals = """      createFn: (data) => {
        // Just send data; DRF will ignore extra fields. If user typed a customer ID, it could be sent.
        return horizonApi.createDeal(data);
      },
      updateFn: (id, data) => {
        return horizonApi.updateDeal(id, data);
      },"""

content = content.replace(old_deals, new_deals)


with open("frontend/src/pages/CRMCoreListView.tsx", "w") as f:
    f.write(content)
