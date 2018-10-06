from setuptools import setup

setup(
    name='helixir',
    version='0.1',
    author='Barney Gale',
    author_email='barney.gale@gmail.com',
    url='https://github.com/barneygale/helixir',
    license='GPL',
    description='Python interface to the Perforce RPC API',
    py_modules=["helixir", "helixir_async"],
)
