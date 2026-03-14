class ChatContext:
    """
    Holds active DB units for a given chat/session.
    Pure routing metadata.
    """

    def __init__(self, active_database_ids: list[str]):
        self.active_database_ids = active_database_ids
