import numpy as np

class ComplexNumberArray:
    """
    Stores a matrix (1D or 2D) of complex samples in a Firestore-safe format:
    
    real_samples = {
        "0": [real values row 0],
        "1": [real values row 1],
        ...
    }

    imag_samples = {
        "0": [imag values row 0],
        "1": [imag values row 1],
        ...
    }
    """

    def __init__(self, complex_samples):
        # Convert to numpy array
        arr = np.asarray(complex_samples)

        # Convert dtype=object → complex64 if needed
        if arr.dtype == object:
            arr = arr.astype(np.complex64)

        # Normalize to 2D: flatten 1D into shape (1, N)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)

        if arr.ndim != 2:
            raise ValueError("complex_samples must be 1D or 2D array-like")

        rows, cols = arr.shape

        # Build Firestore-safe maps
        self.real_samples = {
            str(i): arr[i].real.tolist() for i in range(rows)
        }
        self.imag_samples = {
            str(i): arr[i].imag.tolist() for i in range(rows)
        }

    def to_dict(self):
        """Return Firestore-safe dictionary."""
        return {
            "real_samples": self.real_samples,
            "imag_samples": self.imag_samples,
        }