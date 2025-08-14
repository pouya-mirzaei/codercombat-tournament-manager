

from utils.validators import CSVValidator

class TestCSVValidator(CSVValidator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate(self, csv_file):
        return CSVValidator.validate_csv_file(csv_file)

    def headersMatch(self, csv_file , headers):
        return CSVValidator.validate_csv_headers(csv_file, headers)
