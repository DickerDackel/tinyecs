from setuptools import find_packages, setup

setup(
    name='tinyecs',
    version='0.1.12',
    description='The teeniest, tiniest ECS system',
    author='Michael Lamertz',
    author_email='michael.lamertz@gmail.com',
    url='https://github.com/dickerdackel/tinyecs',
    packages=['tinyecs'],
    install_requires=[
        'cooldown @ git+https://github.com/dickerdackel/cooldown',
    ],
    entry_points={},
)
