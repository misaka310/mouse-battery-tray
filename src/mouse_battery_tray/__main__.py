from .app import main
from .single_instance import acquire_single_instance

if __name__ == "__main__" and acquire_single_instance():
    main()
