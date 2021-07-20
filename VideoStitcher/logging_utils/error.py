###################################################################################
# Copyright (c) 2021 Rhombus Systems                                              #
#                                                                                 # 
# Permission is hereby granted, free of charge, to any person obtaining a copy    #
# of this software and associated documentation files (the "Software"), to deal   #
# in the Software without restriction, including without limitation the rights    #
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell       #
# copies of the Software, and to permit persons to whom the Software is           #
# furnished to do so, subject to the following conditions:                        #
#                                                                                 # 
# The above copyright notice and this permission notice shall be included in all  #
# copies or substantial portions of the Software.                                 #
#                                                                                 # 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR      #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,        #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE     #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER          #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,   #
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE   #
# SOFTWARE.                                                                       #
###################################################################################

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
