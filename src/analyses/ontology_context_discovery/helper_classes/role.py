class Role:
    def __init__(self, label):
        self.label = label
        self.fee: float = 0
        self.fees: list = []

    def calculate_expected_fee(self):
        self.fee = sum(self.fees) / len(self.fees)

        return self.fee
