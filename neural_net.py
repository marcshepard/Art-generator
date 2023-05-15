"""neural_net.py - the engine for generating art from a content and style image.

Given a content image and a style image, generate a new image that combines the
content of the content image with the style of the style image.

The is based on the art-generation-with-nerural-style-transfer" assignment in
Andrew Ng's CNN class:
https://www.coursera.org/learn/convolutional-neural-networks/programming/4AZ8P/art-generation-with-neural-style-transfer
It uses a pre-trained VGG19 model and loss function that is a weighted average of
* Content loss: mean squared error between the content and output images
* Style loss: mean squared error of the gram matrices of the style and output images
An overview of the technique is also here: https://www.tensorflow.org/tutorials/generative/style_transfer
"""

# pylint: disable=invalid-name, line-too-long, too-many-locals, too-many-arguments

from PIL import Image
import numpy as np
import tensorflow as tf

def get_np_images (content_img_path : str, style_img_path : str, size : int):
    """Transform content and style image files to numpy arrays of a given dimension
    content_img_path = path to content image
    style_img_path = path to style image
    size = resize images to size x size
    display = if True, display the images
    """
    content_img = np.array(Image.open(content_img_path).resize((size, size)))
    content_img = tf.constant(np.reshape(content_img, ((1,) + content_img.shape)))
    style_img = np.array(Image.open(style_img_path).resize((size, size)))
    style_img = tf.constant(np.reshape(style_img, ((1,) + style_img.shape)))

    return content_img, style_img

def compute_content_cost(content_output : list, generated_output : list) -> float:
    """
    Computes the content cost function at a given layer
    
    Arguments:
    content_output - a list of images of dimension (1, height, width, channels)
    generated_output -- generated images

    Returns: 
    The squared error between the final content image and the generated image, divided by 4*height*width*channels
    """

    a_C = content_output[-1]    # Get the final content image
    a_G = generated_output[-1]  # Get the final generated image

    # Get the dimensions of a_G
    _, n_H, n_W, n_C = a_G.get_shape().as_list()

    return tf.reduce_sum(tf.square(tf.subtract(a_C, a_G)))/(4*n_H*n_W*n_C)


def compute_layer_style_cost(a_S, a_G):
    """
    Compute the style cost at a given layer

    Arguments:
    a_S -- style image of dimension (1, height, width, channels) after a given layers activation
    a_G -- generated image after a given layers activation

    Returns: 
    The normalized squared error between the style and generated images "gram" matrices; these matrices
    measure the correlation between the different channels of the images
    """

    # Get the dimensions of a_G
    _, n_H, n_W, n_C = a_G.get_shape().as_list()

    # Reshape the tensors from (1, n_H, n_W, n_C) to (n_C, n_H * n_W)
    a_S = tf.reshape(tf.transpose(a_S, perm=[0, 3, 1, 2]), [n_C, n_H*n_W])
    a_G = tf.reshape(tf.transpose(a_G, perm=[0, 3, 1, 2]), [n_C, n_H*n_W])

    # Computing gram_matrices for both images S and G
    GS = tf.matmul(a_S, tf.transpose(a_S))
    GG = tf.matmul(a_G, tf.transpose(a_G))

    # Return the loss
    return tf.reduce_sum(tf.square(tf.subtract(GS, GG)))/(2 * n_C * n_H * n_W)**2

def compute_style_cost(style_image_output, generated_image_output, layers):
    """
    Computes the overall style cost from several chosen layers
    
    Arguments:
    style_image_output -- our tensorflow model
    generated_image_output -- python list containing the content image and the style image
    layers -- A list containing the names of the layers we would like to extract style from
            and a weight for each of them
    
    Returns: The weighted average of the layers style costs
    """

    # initialize the overall style cost
    J_style = 0

    # Set a_S to be the hidden layer activation from the layer we have selected.
    # The last element of the array contains the content layer image, which must not be used.
    a_S = style_image_output[:-1]

    # Set a_G to be the output of the choosen hidden layers.
    # The last element of the list contains the content layer image which must not be used.
    a_G = generated_image_output[:-1]
    for i, weight in zip(range(len(a_S)), layers):  
        # Compute style_cost for the current layer
        J_style_layer = compute_layer_style_cost(a_S[i], a_G[i])

        # Add weight * J_style_layer of this layer to overall style cost
        J_style += weight[1] * J_style_layer

    return J_style

@tf.function()
def total_cost(J_content, J_style, alpha = 10, beta = 40):
    """
    Computes the total cost function
    
    Arguments:
    J_content -- content cost coded above
    J_style -- style cost coded above
    alpha -- hyperparameter weighting the importance of the content cost
    beta -- hyperparameter weighting the importance of the style cost
    
    Returns:
    Weighted average of the content cost and style cost
    """
    return alpha * J_content + beta * J_style

def initialize_generated_image(content_image):
    """Creates a noisy generated image to be used as a starting point for the optimization process"""
    generated_image = tf.Variable(tf.image.convert_image_dtype(content_image, tf.float32))
    noise = tf.random.uniform(tf.shape(generated_image), -0.25, 0.25)
    generated_image = tf.add(generated_image, noise)
    generated_image = clip_0_1(generated_image)
    return generated_image

def clip_0_1(img):
    """
    Truncate all the pixels in the tensor to be between 0 and 1
    
    Arguments:
    image -- Tensor
    J_style -- style cost coded above

    Returns:
    Tensor
    """
    return tf.clip_by_value(img, clip_value_min=0.0, clip_value_max=1.0)

def tensor_to_image(tensor):
    """
    Converts the given tensor into a PIL image
    
    Arguments:
    tensor -- Tensor
    
    Returns:
    Image: A PIL image
    """
    tensor = tensor * 255
    tensor = np.array(tensor, dtype=np.uint8)
    if np.ndim(tensor) > 3:
        assert tensor.shape[0] == 1
        tensor = tensor[0]
    return Image.fromarray(tensor)

class ImageGenerator():
    """Generates an image from a content image and a style image"""
    def __init__(self, trace=print):
        self.training = False
        self.trace = trace

    def cancel(self):
        """Stops the training process"""
        self.training = False

    def generate(self, content_image, style_image, output_image, img_size, epochs, learning_rate) -> str:
        """Runs the neural style transfer algorithm to generate an image of the similar to the content image in the style of the style image"""
        self.training = True
        content, style = get_np_images(content_image, style_image, img_size)
        output = initialize_generated_image(content)
        vgg = tf.keras.applications.VGG19(include_top=False,
                                        input_shape=(img_size, img_size, 3),
                                        weights="imagenet")
        vgg.trainable = False

        STYLE_LAYERS = [
            ('block1_conv1', 0.2),
            ('block2_conv1', 0.2),
            ('block3_conv1', 0.2),
            ('block4_conv1', 0.2),
            ('block5_conv1', 0.2)]

        content_layer = [('block5_conv4', 1)]

        vgg_model_outputs = self._get_layer_outputs(vgg, STYLE_LAYERS + content_layer)

        # Assign the content image to be the input of the VGG model.  
        preprocessed_content =  tf.Variable(tf.image.convert_image_dtype(content, tf.float32))
        a_C = vgg_model_outputs(preprocessed_content)

        # Assign the input of the model to be the "style" image 
        preprocessed_style =  tf.Variable(tf.image.convert_image_dtype(style, tf.float32))
        a_S = vgg_model_outputs(preprocessed_style)

        optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)

        output = tf.Variable(output)

        @tf.function()
        def _train_step(generated_image):
            """Runs one training step and returns the generated image."""
            with tf.GradientTape() as tape:
                # This function uses the precomputed encoded images a_S and a_C

                # Compute a_G as the vgg_model_outputs for the current generated image
                a_G = vgg_model_outputs(generated_image)

                # Compute the style cost
                J_style = compute_style_cost(a_S, a_G, STYLE_LAYERS)

                # Compute the content cost
                J_content = compute_content_cost(a_C, a_G)

                # Compute the total cost
                J = total_cost(J_content, J_style, alpha=10, beta=40)

            grad = tape.gradient(J, generated_image)

            optimizer.apply_gradients([(grad, generated_image)])
            generated_image.assign(clip_0_1(generated_image))

            return J

        # Show the generated image at some epochs
        best_cost = float('inf')
        best_epoch = 0
        for i in range(epochs):
            cost = _train_step(output)
            if cost < best_cost:
                best_cost = cost
                best_epoch = i
            if i % 10 == 0 or i == epochs - 1:
                self.trace(f"Epoch {i}, cost = {cost} ")
            if not self.training:
                break

        if best_epoch != epochs - 1:
            self.trace (f"Optimal cost was {best_cost} at epoch {best_epoch}")
        image = tensor_to_image(output)
        image.save(output_image)
        self.training = False

    @staticmethod
    def _get_layer_outputs(vgg, layer_names):
        """ Creates a vgg model that returns a list of intermediate output values."""
        outputs = [vgg.get_layer(layer[0]).output for layer in layer_names]

        model = tf.keras.Model([vgg.input], outputs)
        return model
