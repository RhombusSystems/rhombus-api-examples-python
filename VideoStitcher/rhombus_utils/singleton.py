class Singleton:
    """A helper class for easily creating singletons. More info: https://stackoverflow.com/questions/31875/is-there-a-simple-elegant-way-to-define-singletons"""

    def __init__(self, decorated):
        self._decorated = decorated

    def get(self):
        """Returns the global instance of a singleton"""
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)
