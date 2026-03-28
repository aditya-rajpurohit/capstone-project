import re


class MetaPlannerMVP:
    MULTI_DB_HINTS = re.compile(r"\b(across|both|compare|merge|combine|join)\b", re.I)

    @classmethod
    def requires_multi_db(cls, user_query: str) -> bool:
        return bool(cls.MULTI_DB_HINTS.search(user_query))
