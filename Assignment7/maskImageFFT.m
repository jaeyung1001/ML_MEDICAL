function maskImageFFT(inputImage, numberOfClicks, filterSize)
img = imread(inputImage);
img_gray = rgb2gray(img);
imshow(img_gray)
waitforbuttonpress;
title('Original Image')
imagesc(abs(fftshift(fft2(img_gray))))
title('Fourier spectrum')
hold on
point = ginput(numberOfClicks);
RGB = insertMarker(abs(fftshift(fft2(img_gray))),point,'o','size',filterSize);
imagesc(RGB)
hold on
imagesc(log(abs(fftshift(fft2(RGB)))))
title('log-transformed')
end