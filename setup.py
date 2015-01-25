from distutils.core import setup, Extension


optimizer = Extension('dinerc', sources=['dinermodule.c'],
                    include_dirs=['/home/tobias/Development/python/source275/Python-2.7.5/Include'],
                    extra_compile_args=['-std=c99'])

setup(name='Circulate',
      version='0.1',
      description='Small web app to group optimization',
      ext_modules=[optimizer], requires=['flask', 'werkzeug'])
