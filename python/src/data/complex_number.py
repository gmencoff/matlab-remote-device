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

        # Store as real and imaginary
        self.real_samples = complex_samples.real.tolist()
        self.imag_samples = complex_samples.imag.tolist()
        

    def to_dict(self):
        """Return Firestore-safe dictionary."""
        return {
            "real_samples": self.real_samples,
            "imag_samples": self.imag_samples
        }
