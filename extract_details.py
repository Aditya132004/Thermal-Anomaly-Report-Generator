import cv2
import numpy as np

thermal_img = cv2.imread("images/thermal/anomaly1_thermal.jpg", cv2.IMREAD_GRAYSCALE)
avg_temp = np.mean(thermal_img)   # average pixel intensity
max_temp = np.max(thermal_img)    # hottest pixel
min_temp = np.min(thermal_img)    # coolest pixel

print("Min:", min_temp, "Max:", max_temp, "Avg:", avg_temp)
