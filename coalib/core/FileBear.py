from coalib.core import Bear


class FileBear(Bear):
    """
    This bear base class parallelizes tasks for each file given.
    """

    def __init__(self, section, file_dict):
        """
        :param section:
            The section object where bear settings are contained. A section
            passed here is considered to be immutable.
        :param file_dict:
            A dictionary containing filenames to process as keys and their
            contents (line-split with trailing return characters) as values.
        """
        Bear.__init__(section)

        self._file_dict = file_dict

        # TODO, especially what about Dependency results?
        # May raise RuntimeError so bear doesn't get executed on invalid params
        self._kwargs =  get_kwargs_for_function(self.analyze, section)

    def generate_tasks(self):
        """
        This method is responsible for providing the job arguments
        ``execute_task`` is called with.

        :return: An iterable containing the positional and keyword arguments
                 organized in pairs: ``(args-tuple, kwargs-dict)``
        """
        return (((filename, file), self._kwargs)
                for filename, file in self._file_dict)
