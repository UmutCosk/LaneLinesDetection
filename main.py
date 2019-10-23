import cv2
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import math
import helpers
import collections


# images = os.listdir("test_images/")
# Load Image
# path = images[5]
# img1 = cv2.imread("test_images/"+path)
#cap = cv2.VideoCapture("test_videos/solidWhiteRight.mp4")
cap = cv2.VideoCapture("test_videos/challenge.mp4")
#cap = cv2.VideoCapture("test_videos/solidYellowLeft.mp4")
"""Settings"""
lower_yellow = np.array([10, 125, 175])
up_yellow = np.array([40, 255, 255])
sensivity = 30
lower_white = np.array([0, 0, 255 - sensivity])
up_white = np.array([255, sensivity, 255])

"""Resize"""
_, img1 = cap.read()
height, width, _ = img1.shape
width = int(width / 1.2)
height = int(height / 1.2)

"""Region of Interest"""
vertices = np.array([((int(width * 0.05), int(height * 1)),
                      (int(width * 0.4), int(height * 0.6)),
                      (int(width * 0.6), int(height * 0.6)),
                      (int(width * 0.95), int(height * 1)))])
vertices_left = np.array([((int(width * 0.05), int(height * 1)),
                           (int(width * 0.45), int(height * 0.6)),
                           (int(width * 0.475), int(height * 0.6)),
                           (int(width * 0.4), int(height * 1)))])
vertices_right = np.array([((int(width * 0.95), int(height * 1)),
                            (int(width * 0.55), int(height * 0.60)),
                            (int(width * 0.525), int(height * 0.6)),
                            (int(width * 0.6), int(height * 1)))])

"""Perspective Transformation"""
src = np.float32(
    [((int(width * 0.05), int(height * 1)),
        (int(width * 0.4), int(height * 0.6)),
        (int(width * 0.6), int(height * 0.6)),
        (int(width * 0.95), int(height * 1)))]
)
dst = np.float32(
    [((int(width * 0), int(height * 1)),
        (int(width * 0), int(height * 0)),
        (int(width * 1), int(height * 0)),
        (int(width * 1), int(height * 1)))]
)
M = cv2.getPerspectiveTransform(src, dst)
"""Lane Stabilizer"""
bl = []
br = []
ml = []
mr = []
check_values = 40


def get_mean(mylist, new_value):
    if(len(mylist) == 0):
        for i in range(check_values):
            mylist.append(new_value)
    else:
        del mylist[0]
        mylist.append(new_value)
    return np.median(mylist)


"""Main Loop"""
while(cap.isOpened()):
    # Capture frame-by-frame
    ret, img1 = cap.read()
    if not ret:
        break

    img1 = cv2.resize(img1, (width, height),
                      interpolation=cv2.INTER_AREA)
    result = img1
    # 1.1 Color Thresholding
    hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV)
    mask_yellow = cv2.inRange(hsv, lower_yellow, up_yellow)
    mask_white = cv2.inRange(hsv, lower_white, up_white)
    mask = mask_white + mask_yellow

    # 2 Canny
    result = cv2.Canny(mask, 50, 200)
    canny = result
    # 3 Region of Interest
    result = helpers.region_of_interest(result, vertices)
    left = helpers.region_of_interest(img1, vertices_left)
    right = helpers.region_of_interest(img1, vertices_right)
    roi = result
    # 4 Hough Transform
    try:
        result = helpers.hough_lines(
            result, 1.89, np.pi / 180, 25, 25, 125)  # hier noch interpolieren
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    except:
        pass
        # kernel = np.ones((5, 5), np.uint8)
        # result = cv2.morphologyEx(result, cv2.MORPH_CLOSE,
        #                           kernel, dst=None, anchor=None,
        #                           iterations=20)
     # 5 Prespective Transformation
    gray = helpers.grayscale(result)
    warped = cv2.warpPerspective(
        gray, M, (width, height), flags=cv2.INTER_LINEAR)
    # test = warped[int(height/2):height][0:width]
    histogram = np.sum(warped, axis=0)
    # plt.cla()
    # plt.plot(histogram)
    # plt.pause(0.01)
    out_img = warped
    midpoint = np.int(histogram.shape[0]//2)
    leftx_base = np.argmax(histogram[:midpoint])
    rightx_base = np.argmax(histogram[midpoint:]) + midpoint
    # Hyperparamters
    # Choose the number of sliding windows
    nwindows = 12
    # Set the width of the windows +/- margin
    margin = 75
    # Set minimum number of pixels found to recenter window
    minpix = 1000
    # Set height of windows - based on nwindows above and image shape
    window_height = np.int(height//nwindows)
    # Identify the x and y positions of all nonzero (i.e. activated) pixels in the image
    nonzero = warped.nonzero()
    nonzeroy = np.array(nonzero[0])
    nonzerox = np.array(nonzero[1])
    # Current positions to be updated later for each window in nwindows
    leftx_current = leftx_base
    rightx_current = rightx_base
    # Create empty lists to receive left and right lane pixel indices
    left_lane_inds = []
    right_lane_inds = []

    for w in range(nwindows-1):
        test2 = warped[int(height - (w+1) * window_height):height - (w) * window_height][0:width]
        histogram = np.sum(test2, axis=0)
        midpoint = np.int(histogram.shape[0]//2)
        leftx_base = np.argmax(histogram[:midpoint])
        rightx_base = np.argmax(histogram[midpoint:]) + midpoint
        win_y_low = (height - w * window_height)
        win_y_high = (height - w * window_height - window_height)
        win_xleft_low = leftx_base - margin
        win_xleft_high = leftx_base + margin
        win_xright_low = rightx_base - margin
        win_xright_high = rightx_base + margin

        nonzero = warped.nonzero()
        nonzeroy = np.array(nonzero[0])
        nonzerox = np.array(nonzero[1])
        good_left_inds = ((nonzeroy <= win_y_low) & (nonzeroy > win_y_high) &
                          (nonzerox >= win_xleft_low) & (nonzerox < win_xleft_high)).nonzero()[0]
        good_right_inds = ((nonzeroy <= win_y_low) & (nonzeroy > win_y_high) &
                           (nonzerox >= win_xright_low) & (nonzerox < win_xright_high)).nonzero()[0]
        print(len(good_left_inds), len(good_right_inds))
        if(len(good_left_inds) > minpix):
            cv2.rectangle(out_img, (win_xleft_low, win_y_low),
                          (win_xleft_high, win_y_high), (255, 0, 0), 3)
        if(len(good_right_inds) > minpix):
            cv2.rectangle(out_img, (win_xright_low, win_y_low),
                          (win_xright_high, win_y_high), (255, 0, 0), 3)
        #cv2.imshow("test222", test2)
        # if cv2.waitKey(0) & 0xFF == ord('q'):
        #     continue

    # dy = 15
    # dx = 15
    # xl = []
    # yl = []
    # xr = []
    # yr = []
    # for y in range(height - 1, int(height * 0.6), -dy):
    #     for x in range(0, int(width / 2), dx):
    #         if(gray[y][x] > 150):
    #             for ddx in range(x, int(width / 2), 2):
    #                 if(gray[y - dy * 2][ddx] > 150):
    #                     xl.append(ddx)
    #                     yl.append(y - dy * 2)
    #     for x in range(width - 1, int(width / 2), -dx):
    #         if(gray[y][x] > 150):
    #             for ddx in range(x, int(width / 2), -2):
    #                 if(gray[y - dy * 2][ddx] > 150):
    #                     xr.append(ddx)
    #                     yr.append(y - dy * 2)
    # # for i in range(len(pts_left)):
    # #     cv2.line(img1, pts_left[i], pts_left2[i], (255, 255, 0), 1)
    # m = 0
    # b = 0
    # """Draw left lane"""
    # m, b = np.polyfit(xl, yl, 1)
    # bl.append(b)
    # if(abs(m) > 0.2 and abs(m) < 2):
    #     ml.append(m)
    # b = get_mean(bl, b)
    # m = get_mean(ml, m)

    # for y1 in range(int(height), int(height * 0.625), -dy):
    #     y2 = y1 - dy
    #     x1 = int((y1 - b) / m)
    #     x2 = int((y2 - b) / m)
    #     cv2.line(img1, (x2, y2), (x1, y1), (250, 255, 0), 5)

    # """Draw right lane"""
    # if(not len(xr) == 0):
    #     m, b = np.polyfit(xr, yr, 1)
    #     br.append(b)
    #     if(abs(m) > 0.2 and abs(m) < 2):
    #         mr.append(m)
    #     b = get_mean(br, b)
    #     m = get_mean(mr, m)
    # else:
    #     b = get_mean(br, br[len(br) - 1])
    #     m = get_mean(mr, mr[len(mr) - 1])

    # for y1 in range(int(height), int(height * 0.625), -dy):
    #     y2 = y1 - dy
    #     x1 = int((y1 - b) / m)
    #     x2 = int((y2 - b) / m)
    #     cv2.line(img1, (x2, y2), (x1, y1), (250, 255, 0), 5)

    # Show Result
    cv2.imshow("Lane Line Detection", img1)
    #cv2.imshow("Warped", warped)
    cv2.imshow("test",   out_img)
    if cv2.waitKey(0) & 0xFF == ord('q'):
        continue


cap.release()
cv2.destroyAllWindows()
