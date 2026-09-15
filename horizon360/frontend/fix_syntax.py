with open("frontend/src/pages/CRMCoreListView.tsx", "r") as f:
    content = f.read()

content = content.replace(") : {field.type === 'select' ? (", ") : field.type === 'select' ? (")
# Need to remove the extra curly brace at the end of the select condition
content = content.replace("                        />\n                      )}", "                        />\n                      )")
content = content.replace(") :\n                      {field.type", ") :\n                      field.type")


with open("frontend/src/pages/CRMCoreListView.tsx", "w") as f:
    f.write(content)
