import numpy as np
from main import softmax


def test_softmax():
    """Test the softmax function."""
    # Test case 1: simple case
    x = np.array([1.0, 2.0, 3.0])
    expected_output = np.array([0.09003057, 0.24472847, 0.66524096])
    np.testing.assert_almost_equal(softmax(x), expected_output, decimal=5)

    # Test case 2: all zeros
    x = np.array([0.0, 0.0, 0.0])
    expected_output = np.array([1 / 3, 1 / 3, 1 / 3])
    np.testing.assert_almost_equal(softmax(x), expected_output, decimal=5)

    # Test case 3: large numbers
    x = np.array([1000.0, 1001.0, 1002.0])
    expected_output = np.array([0.09003057, 0.24472847, 0.66524096])
    np.testing.assert_almost_equal(softmax(x), expected_output, decimal=5)

    # # Test case 4: negative numbers
    # x = np.array([-1.0, -2.0, -3.0])
    # expected_output = np.array([0.66524096, 0.24472847, 0.09003057])
    # np.testing.assert_almost_equal(softmax(x), expected_output, decimal=5)
