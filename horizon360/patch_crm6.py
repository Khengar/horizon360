import re

with open("frontend/src/pages/CRMCoreListView.tsx", "r") as f:
    content = f.read()

# Change Create button to Add
old_btn = "<Plus className=\"w-4 h-4\" /> Create {config.title.slice(0, -1)}"
new_btn = "<Plus className=\"w-4 h-4\" /> Add {config.title.slice(0, -1).replace('ie', 'y')}"
content = content.replace(old_btn, new_btn)

# Fix singular titles: Companie -> Company
old_title = "{modalMode === 'create' ? 'Add' : modalMode === 'edit' ? 'Edit' : 'View'} {config.title.slice(0, -1)}"
new_title = "{modalMode === 'create' ? 'Add' : modalMode === 'edit' ? 'Edit' : 'View'} {config.title.endsWith('ies') ? config.title.slice(0, -3) + 'y' : config.title.slice(0, -1)}"
content = content.replace(old_title, new_title)

# Also fix success messages
old_succ = "Successfully created ${config.title.slice(0, -1)}"
new_succ = "Successfully created ${config.title.endsWith('ies') ? config.title.slice(0, -3) + 'y' : config.title.slice(0, -1)}"
content = content.replace(old_succ, new_succ)

old_succ2 = "Successfully updated ${config.title.slice(0, -1)}"
new_succ2 = "Successfully updated ${config.title.endsWith('ies') ? config.title.slice(0, -3) + 'y' : config.title.slice(0, -1)}"
content = content.replace(old_succ2, new_succ2)

# Fix save button
old_save = "Save {config.title.slice(0, -1)}"
new_save = "Save {config.title.endsWith('ies') ? config.title.slice(0, -3) + 'y' : config.title.slice(0, -1)}"
content = content.replace(old_save, new_save)


# One more button fix for Add Company
old_btn2 = "<Plus className=\"w-4 h-4\" /> Add {config.title.slice(0, -1).replace('ie', 'y')}"
new_btn2 = "<Plus className=\"w-4 h-4\" /> Add {config.title.endsWith('ies') ? config.title.slice(0, -3) + 'y' : config.title.slice(0, -1)}"
content = content.replace(old_btn2, new_btn2)


with open("frontend/src/pages/CRMCoreListView.tsx", "w") as f:
    f.write(content)
