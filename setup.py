from setuptools import find_packages,setup

setup(name="School-Chatbot",
       version="0.0.1",
       author="Uzair khan",
       author_email="uzairu471@gmail.com",
       packages=find_packages(),
       install_requires=['langchain-astradb','langchain'])