from translate import Translator

translator = Translator(to_lang="vi")

with open("custom_addons/mhd_ohrms_overtime/models/mhd_hr_payroll_community.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

    

new_lines = []
msgid = None

for line in lines:
    if line.startswith("msgid "):
        msgid = line.strip().split(" ", 1)[1].strip('"')
    elif line.startswith("msgstr ") and msgid and line.strip() == 'msgstr ""':
        translated = translator.translate(msgid)
        line = f'msgstr "{translated}"\n'
        msgid = None
    new_lines.append(line)

with open("vi_VN_mhd.po", "w", encoding="utf-8") as f:
    f.writelines(new_lines)
