import re
with open("src/pages/CRMCoreListView.tsx", "r") as f:
    text = f.read()

text = re.sub(r'render: \(_val, row\) =>', r'render: (val, row) =>', text)
text = re.sub(r"render: \(_val\) =>", r"render: (val) =>", text)

with open("src/pages/CRMCoreListView.tsx", "w") as f:
    f.write(text)
