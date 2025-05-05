from setuptools import setup, find_packages

setup(
    name="led_driver_rs485",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pyserial",
        "playsound",
        "PyObjC",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "led-driver=main:main",
        ],
    },
)
