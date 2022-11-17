class MockCodeConverter:
    def get_mbs_item_fee(self, code):
        return 2 ** int(code), None
