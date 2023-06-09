import re


def keep_json_format(content: str):
    try:
        pattern = r'{(.*?)}'
        match = re.search(pattern, content, re.DOTALL)
        extracted_content = match.group(0)
        return extracted_content
    except:
        return "Error"
