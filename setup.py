from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='pdf-atomic-pro',
    version='0.1.0',
    packages=find_packages(),
    py_modules=['start_gui'],
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'pdf-atomic-pro=start_gui:main'
        ]
    },
    author='Jules',
    author_email='',
    description='A tool to convert PDF files into a structured Obsidian vault.',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/example/pdf-atomic-pro',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
