class BaseReportSerializer:

    def __init__(self, record):
        self.record = record

    def serialize(self):
        raise NotImplementedError