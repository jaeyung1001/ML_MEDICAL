clc

img = imread('fourier.png');
img_gray = rgb2gray(img);
subplot(1,3,1);
imagesc(abs(fftshift(fft2(img))))
title('Original Image');
subplot(1,3,2);
imagesc(abs(fftshift(fft2(img_gray))))
title('GrayScale Image');
subplot(1,3,3);
imagesc(log(abs(fftshift(fft2(img_gray)))))
title('log-transformed Image');
%imshow(after_img_gray)