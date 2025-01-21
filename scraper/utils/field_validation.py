import re
from datetime import datetime

import re
from datetime import datetime

def parse_date(date_str):
    try:
        # Clean the date string: remove non-date parts like "Publish Date：" or extra spaces
        date_str_cleaned = re.sub(r"[^\w\s\-:]", "", date_str).strip()  # Remove non-alphanumeric characters except - and :
        date_str_cleaned = re.sub(r"Publish Date|Closing Date", "", date_str_cleaned, flags=re.IGNORECASE).strip()

        # Parse the cleaned date string
        return datetime.strptime(date_str_cleaned, "%b-%d-%Y")
    except ValueError:
        raise ValueError(f"Cannot parse date: {date_str}")


def prepare_list_field(field):
        if isinstance(field, list):
            return field
        elif isinstance(field, str):
            return [field.strip()]
        return []