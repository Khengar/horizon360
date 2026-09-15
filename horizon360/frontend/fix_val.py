import re
with open("src/pages/CRMCoreListView.tsx", "r") as f:
    text = f.read()

# Replace unused val with _val
text = re.sub(r'render:\s*\(val,\s*row\)\s*=>\s*row', r'render: (_val, row) => row', text)
text = re.sub(r"render:\s*\(val\)\s*=>\s*'-'", r"render: (_val) => '-'", text)
text = re.sub(r"render:\s*\(\)\s*=>\s*'-'", r"render: (_val) => '-'", text) # in case I left some empty

with open("src/pages/CRMCoreListView.tsx", "w") as f:
    f.write(text)
