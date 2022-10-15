class MutationError(Exception):
    def __init__(self, *args):
        super().__init__(' '.join([str(_) for _ in args]))