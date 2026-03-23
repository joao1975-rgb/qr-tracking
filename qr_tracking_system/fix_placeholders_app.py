import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure to avoid breaking query strings like `/track?campaign=`
# Normally SQL placeholders have spaces around them or at the end of string or right before quotes.
# This regex targets ? that are used as SQL placeholders:
# ` = ?`
# `, ?`
# `(?,`
# `?)`
# `LIMIT ?`
# `OFFSET ?`
# The safer way to do this is to replace these precise patterns:

content = re.sub(r' \= \?', ' = %s', content)
content = re.sub(r'\((\s*)\?(\s*)\)', r'(\1%s\2)', content)
content = re.sub(r'\((\s*)\?', r'(\1%s', content)
content = re.sub(r'\,(\s*)\?', r',\1%s', content)
content = re.sub(r'LIMIT \?', 'LIMIT %s', content)
content = re.sub(r'OFFSET \?', 'OFFSET %s', content)
content = content.replace('>= ?', '>= %s')
content = content.replace('<= ?', '<= %s')
content = content.replace('!= ?', '!= %s')

# Also fix `active = 1` -> `active = TRUE`
# And `active = 0` -> `active = FALSE`
content = content.replace('active = 1', 'active = TRUE')
content = content.replace('active = 0', 'active = FALSE')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Finished fixing placeholders and booleans in app.py")
