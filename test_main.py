import pandas as pd
import numpy as np
import unittest

from main import rate_of_change as roc

class test_rate_of_change(unittest.TestCase):
    def ambient_temp_test(self):
        sample_test = pd.DataFrame({
            'ambientTemp': [10, 20, 30, 40],
            'missionTime': [1, 2, 3, 4]
        })
        
        roc_ambient = roc(sample_test, col='ambientTemp')
        expected_ambient = pd.Series([np.nan, 10, 10, 10])
        pd.testing.assert_series_equal(roc_ambient, expected_ambient)        

if __name__ == '__main__':
    unittest.main()