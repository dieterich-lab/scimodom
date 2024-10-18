from io import BytesIO, StringIO


class MockStringIO(StringIO):
    def __init__(self, **kargs):
        super(MockStringIO, self).__init__(**kargs)
        self.final_content = None

    def close(self):
        self.final_content = self.getvalue()
        super(MockStringIO, self).close()


class MockBytesIO(BytesIO):
    def __init__(self, **kargs):
        super(MockBytesIO, self).__init__(**kargs)
        self.final_content = None

    def close(self):
        self.final_content = self.getvalue()
        super(MockBytesIO, self).close()
