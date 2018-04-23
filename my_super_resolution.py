# coding: utf-8

import numpy as np
import cv2
from skimage.measure import compare_ssim, compare_mse, compare_psnr
from utils.super_resolution_utils import *
from utils.cpp_grad_utils import *


# Open original image
im_bgr = cv2.imread('hedgehog.jpg')
im = im_bgr.astype(np.float)

roi = im[500:900, 800:1300]

# Set important variables
iterations = 20
q = 2
nb_lr_im = 8
noise = 0.1*(np.max(roi) - np.min(roi))
l = 0.2
beta = 0.5
exp_file = 'experiences.txt'

with open(exp_file, 'a') as f:
    f.write("#Conditions de l'expérience:")
    f.write("#q={}, nb_lr_images={}, lambda={}, beta={}, nb_iterations={}".format(q, nb_lr_im, l, beta, iterations))

# Create small images and store them somewhere on disk. Should work for gray and color images
lr_images = createLRrSamples(roi, nb_lr_images=nb_lr_im, q=q, noise_variance=noise)
for i in range(lr_images.shape[0]):
    cv2.imwrite('lr_images/lr_'+str(i)+'.png', lr_images[i])

# Create new empty HR image. Should work for color and gray images
hr_dims = get_hr_dims(lr_images.shape, q)
hr_image = np.zeros(hr_dims)

for iteration in range(iterations):

    # Compute directional order 1 and 2 gradients
    Ix = grad_x(hr_image)
    Iy = grad_y(hr_image)
    Ixy = grad_y(Ix)
    Ixx = grad_xx(hr_image)
    Iyy = grad_yy(hr_image)

    #Compute data fidelity energy gradient, denoising energy gradient, smoothing energy gradient
    data_fidelity_gradient = data_fidelity_gradient(hr_image, lr_images, q)
    denoising_gradient = TV_regularization(Ix, Iy, Ixy, Ixx, Iyy, beta)
    smoothing_gradient = heat_gradient(Ix, Iy, Ixy, Ixx, Iyy)

    #Compute weighting factor
    tau = compute_tau_1(Ix, Iy, 0.6)
    #tau = compute_tau_2(Ix, Iy)
    #tau = compute_tau_3(Ix, Iy, 0.6)

    #Update HR image: apply gradients to image
    hr_im += dt*(data_fidelity_gradient + l*(tau*denoising_gradient + (1-tau)*smoothing_gradient))

    if iteration % 5 == 0:
        mse = compare_mse(roi, hr_im)
        ssim = compare_ssim(roi, hr_im)
        psnr = compare_psnr(roi, hr_im, data_range=255.0)
        name = 'hr_images/hr_'+str(iteration)+'.png'
        cv2.imwrite(name, hr_image)
        with open(exp_file, 'a') as f:
            f.write("{}\t{}\t{}\t{}".format(iteration, mse, ssim, psnr, name))
        #TODO: make matplotlib graph with metrics in title ?
        print(iteration)