

class FunboostBaseConcurrentPool:

    def __deepcopy__(self, memodict={}):
        """
        Pydantic's default type declaration requires objects to support deepcopy
        """
        return self