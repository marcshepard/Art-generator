art_generator.py - produce an image from a content and style picture

The generated image will be similar to the content image, but with the style of the style image.
This file provides a graphical user interface for the neural_net.py code, which is based on
Andrew Ng's Coursera course on Convolutional Neural Networks. 

A prereq to running art_generator.py is:
* Clone this repository. https://www.w3schools.com/git/git_remote_getstarted.asp. Or just copy anonymizer.py
* Install a recent version of Python from https://www.python.org/downloads/. This script has been tested with Python 3.10
* Add Python to your path. See https://datatofish.com/add-python-to-windows-path/.
* Install the following optional packages from a cmd window (launched after Python has been added to your path):
    * PIL - Python image library
    * Tensorflow - a library for neural net deep learning