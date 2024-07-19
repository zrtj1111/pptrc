# -*- coding: utf-8 -*-
# @Time    : 2024/7/19 下午3:18 下午3:18
# @Author  : Zr
# @Comment :


from setuptools import find_packages, setup

requirements = [
    "chardet"
]

setup(
    name='pptrc',
    version="0.0.1",
    description='puppeteer异步转同步',
    packages=find_packages(exclude=[]),
    author='Zr',
    author_email='zrtj1111@hotmail.com',
    license='Apache License v2',
    include_package_data=True,
    package_data={
        'pptrc': ['js/*.js', 'js/package.json'],
    },
    url='https://github.com/zrtj1111',
    install_requires=requirements,
    classifiers=[
        'Programming Language :: Python',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    python_requires=">=3.6"
)
