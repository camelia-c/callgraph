from setuptools import setup

setup(name='callgraph',
      version='1.0.0',
      description='Callgraph is a Python package that defines a decorator, and Jupyter magic, to draw dynamic call graphs of Python function calls',
      url_original='https://github.com/osteele/callgraph',
      author='oliversteele',
      author_email='',
      license='MIT',
      packages=['callgraph'],
      install_requires=['graphviz','IPython'],
      zip_safe=False)

