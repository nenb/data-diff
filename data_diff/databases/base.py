from data_diff.sqeleton.databases import AbstractMixin_MD5, AbstractMixin_NormalizeValue


class DatadiffDialect(AbstractMixin_MD5, AbstractMixin_NormalizeValue):
    pass
