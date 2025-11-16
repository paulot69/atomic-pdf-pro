from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='pdf-to-obsidian',
    version='0.1.0',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'pdf-to-obsidian=app.cli:main'
        ]
    },
    author='Jules',
    author_email='',
    description='A tool to convert PDF files into a structured Obsidian vault.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/example/pdf-to-obsidian', # Placeholder URL
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
