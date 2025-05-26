try:
    from citylink.core import EmbeddedCore, main

    main()
except ImportError:
    print("No main module found. Proceding with initialization.")
except Exception as e:
    raise e

from machine import soft_reset

print("CityLink EmbeddedCore failed. Resetting the device...")
soft_reset()
