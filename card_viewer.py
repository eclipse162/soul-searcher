"""
Card Detection
--------------
This program detects a card from given input.
Reference used:
https://www.geeksforgeeks.org/detect-an-object-with-opencv-python/
"""
import cv2
from matplotlib import pyplot as plt

def main():
    image_name = "test.jpg"
    img = cv2.imread(image_name)

    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # TODO: create haar cascade for card detection
    plt.subplot(1,1,1)
    plt.imshow(img_rgb)
    plt.show()


main()