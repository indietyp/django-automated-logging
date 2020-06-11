from collections import namedtuple


def namedtuple2dict(root: namedtuple) -> dict:
    """
    transforms nested namedtuple into a dict

    :param root: namedtuple to convert
    :return: dictionary from namedtuple
    """
    return {
        k: v if not isinstance(v, tuple) else namedtuple2dict(v)
        for k, v in root._asdict().items()
    }
