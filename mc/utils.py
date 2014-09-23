# -*- coding: utf-8 -*-

def generate_password():
    import string
    from random import sample
    chars = string.letters + string.digits
    return ''.join(sample(chars, 8))


# Local Variables: **
# comment-column: 56 **
# indent-tabs-mode: nil **
# python-indent: 4 **
# End: **
