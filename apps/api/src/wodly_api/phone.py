import re

_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_E164 = re.compile(r"^\+[1-9]\d{7,14}$")


def normalize_phone(raw: str) -> str:
    phone = re.sub(r"[\s\-()]", "", raw.translate(_DIGITS))
    if re.fullmatch(r"09\d{9}", phone):
        phone = "+98" + phone[1:]
    elif phone.startswith("0098"):
        phone = "+" + phone[2:]
    if not _E164.fullmatch(phone):
        raise ValueError("invalid phone number")
    return phone
