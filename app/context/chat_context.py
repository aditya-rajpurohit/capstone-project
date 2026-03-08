
class ChatContext:
    """
    Holds active DB units for a given chat/session.
    Pure routing metadata.
    """

    def __init__(self, active_db_ids: list[str]):
        self.active_db_ids = active_db_ids
