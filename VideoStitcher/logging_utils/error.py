class NumpyArrayError(Exception):
    """Exception raised for errors in numpy arrays

    :attribute expression: Input expression in which the error occurred
    :attribute message: Explanation of the error
    """

    expression: str
    message: str

    def __init__(self, expression: str, message: str):
        """Constructor for an input error

        :param expression: Input expression in which the error occurred
        :param message: Explanation of the error
        """
        self.expression = expression
        self.message = message

class NonNormalizedVectorError(Exception):
    """Exception raised for a provided vector that is not normalized

    :attribute expression: Input expression in which the error occurred
    :attribute message: Explanation of the error
    """

    expression: str
    message: str

    def __init__(self, expression: str, message: str):
        """Constructor for an input error

        :param expression: Input expression in which the error occurred
        :param message: Explanation of the error
        """
        self.expression = expression
        self.message = message
