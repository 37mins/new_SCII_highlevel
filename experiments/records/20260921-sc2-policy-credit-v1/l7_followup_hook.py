"""Only compose existing short and long observers; no policy intervention."""
import os


def install():
    if os.environ['SC2_ACCEPTANCE_STAGE'] in ('pre', 'train2', 'post'):
        from acceptance_hook import install as observe
    else:
        from qwen_l7_long_hook import install as observe
    observe()
