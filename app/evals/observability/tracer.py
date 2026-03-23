import uuid


class TraceContext:

    def __init__(self):
        self.trace_id = str(uuid.uuid4())
