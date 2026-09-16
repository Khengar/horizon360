import re

with open("frontend/src/pages/CRMCoreListView.tsx", "r") as f:
    content = f.read()

# Add select rendering
old_input = """                      <input
                        type={field.type || 'text'}
                        name={field.name}
                        value={formData[field.name] || ''}
                        onChange={handleInputChange}
                        required={field.required}
                        className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-brand-500 text-gray-800"
                        placeholder={`Enter ${field.label.toLowerCase()}`}
                      />"""

new_input = """                      {field.type === 'select' ? (
                        <select
                          name={field.name}
                          value={formData[field.name] || ''}
                          onChange={handleInputChange}
                          required={field.required}
                          className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-brand-500 text-gray-800"
                        >
                          <option value="">Select...</option>
                          {field.options?.map(opt => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                          ))}
                        </select>
                      ) : (
                        <input
                          type={field.type || 'text'}
                          name={field.name}
                          value={formData[field.name] || ''}
                          onChange={handleInputChange}
                          required={field.required}
                          className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-brand-500 text-gray-800"
                          placeholder={`Enter ${field.label.toLowerCase()}`}
                        />
                      )}"""

content = content.replace(old_input, new_input)

# Update fields definitions to include options and type: 'select'
old_emp_fields = """      fields: [
        { name: 'first_name', label: 'First Name', required: true },
        { name: 'last_name', label: 'Last Name', required: true },
        { name: 'email', label: 'Email', type: 'email', required: true },
        { name: 'role', label: 'Role / Job Title', required: true },
        { name: 'status', label: 'Status' }
      ]"""
new_emp_fields = """      fields: [
        { name: 'first_name', label: 'First Name', required: true },
        { name: 'last_name', label: 'Last Name', required: true },
        { name: 'email', label: 'Email', type: 'email', required: true },
        { name: 'role', label: 'Role / Job Title', required: true },
        { name: 'status', label: 'Status', type: 'select', options: [
            { value: 'active', label: 'Active' },
            { value: 'on_leave', label: 'On Leave' },
            { value: 'terminated', label: 'Terminated' }
        ]}
      ]"""
content = content.replace(old_emp_fields, new_emp_fields)

old_prod_fields = """      fields: [
        { name: 'name', label: 'Product Name', required: true },
        { name: 'sku', label: 'SKU' },
        { name: 'price', label: 'Price', type: 'number', required: true },
        { name: 'description', label: 'Description' },
        { name: 'is_active', label: 'Status' }
      ]"""
new_prod_fields = """      fields: [
        { name: 'name', label: 'Product Name', required: true },
        { name: 'sku', label: 'SKU' },
        { name: 'price', label: 'Price', type: 'number', required: true },
        { name: 'description', label: 'Description' },
        { name: 'is_active', label: 'Status', type: 'select', options: [
            { value: 'true', label: 'Active' },
            { value: 'false', label: 'Inactive' }
        ]}
      ]"""
content = content.replace(old_prod_fields, new_prod_fields)

old_deal_fields = """      fields: [
        { name: 'title', label: 'Deal Name', required: true },
        { name: 'company', label: 'Company/Customer' },
        { name: 'stage', label: 'Stage' },
        { name: 'value', label: 'Amount', type: 'number', required: true },
        { name: 'expected_close_date', label: 'Expected Close Date', type: 'date' },
        { name: 'owner', label: 'Owner' },
        { name: 'description', label: 'Description' }
      ]"""
new_deal_fields = """      fields: [
        { name: 'title', label: 'Deal Name', required: true },
        { name: 'company', label: 'Company/Customer' },
        { name: 'stage', label: 'Stage', type: 'select', options: [
            { value: 'visitor', label: 'Visitor' },
            { value: 'lead', label: 'Lead' },
            { value: 'opportunity', label: 'Opportunity' },
            { value: 'proposal', label: 'Proposal' },
            { value: 'won', label: 'Won' },
            { value: 'lost', label: 'Lost' }
        ]},
        { name: 'value', label: 'Amount', type: 'number', required: true },
        { name: 'expected_close_date', label: 'Expected Close Date', type: 'date' },
        { name: 'owner', label: 'Owner' },
        { name: 'description', label: 'Description' }
      ]"""
content = content.replace(old_deal_fields, new_deal_fields)


# Add options to interface
content = content.replace("fields: { name: string; label: string; type?: string; required?: boolean }[];", 
                          "fields: { name: string; label: string; type?: string; required?: boolean; options?: {value: string, label: string}[] }[];")

with open("frontend/src/pages/CRMCoreListView.tsx", "w") as f:
    f.write(content)
