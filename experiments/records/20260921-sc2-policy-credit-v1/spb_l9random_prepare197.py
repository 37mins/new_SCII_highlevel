"""Single no-GPU preparation; failures preserve this RUN_ID and block queueing."""
import spb_l9random197 as m
from spb_l8random_prepare197 import main

if __name__=='__main__':
    main(m,'spb_l9random197.py','spb_l9random_eval197.py',terminal_probe=True)
