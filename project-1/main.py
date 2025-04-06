import numpy as np
import numpy.typing as npt


def softmax(x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    """Compute the softmax of vector x by numerically stable method.

    Args:
        x (npt.NDArray): Input array.
    """
    # subtract max for numerical stability
    x = x - np.max(x)
    e_x = np.exp(x)
    return e_x / np.sum(e_x, axis=0)


def main():
    """Main function to demonstrate the softmax function."""
    x = np.array([1.0, 2.0, 3.0])
    print("Input:", x)
    print("Softmax output:", softmax(x))


if __name__ == "__main__":
    main()
