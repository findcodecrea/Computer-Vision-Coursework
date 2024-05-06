from utils import setup_logging, check_file
import cv2
import numpy as np

# Increase minimum match count for better stability in homography calculation
MIN_MATCH_COUNT = 20
FLANN_INDEX_KDTREE = 0
index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
search_params = dict(checks=50)
setup_logging()


def stitch_images(img1, img2):
    # Initiate SIFT detector
    detector = cv2.SIFT.create()

    # find the keypoints and descriptors about these two pictures
    kp1, des1 = detector.detectAndCompute(img1, None)
    kp2, des2 = detector.detectAndCompute(img2, None)

    matcher = cv2.FlannBasedMatcher(index_params, search_params)
    matches = matcher.knnMatch(des1, des2, k=2)

    # store all the good matches as per Lowe's ratio test.
    matches_after_test = []
    for m, n in matches:
        # Lowe's ratio test - increase threshold for better match quality
        if m.distance < 0.75 * n.distance:
            matches_after_test.append(m)
    if len(matches_after_test) < MIN_MATCH_COUNT:
        print("Not enough matches are found - {}/{}".format(len(matches_after_test), MIN_MATCH_COUNT))
        return img1

    last_points = np.float32([kp1[m.queryIdx].pt for m in matches_after_test]).reshape(-1, 1, 2)
    latter_points = np.float32([kp2[m.trainIdx].pt for m in matches_after_test]).reshape(-1, 1, 2)

    w = img2.shape[1]
    h = img2.shape[0]
    offset_x = img1.shape[1]
    offset_y = img1.shape[1]

    latter_pt_final = latter_points.copy()
    latter_pt_final[:, :, 0] = latter_pt_final[:, :, 0] + offset_x
    latter_pt_final[:, :, 1] = latter_pt_final[:, :, 1] + offset_y
    check, mask = cv2.findHomography(last_points, latter_pt_final, cv2.RANSAC, 5.0)
    if check is None:
        print("Homography could not be computed.")
        return img1

    img_final = cv2.warpPerspective(img1, check, (w + offset_x, h + offset_y))

    for i in range(h):
        for j in range(w):
            # Weighted blending to reduce seam visibility
            alpha = 0.5  # Weighting factor, can be adjusted
            if np.all(img_final[i + offset_y][j + offset_x] == 0):
                img_final[i + offset_y][j + offset_x] = img2[i][j]
            elif np.all(img2[i][j] != 0):
                img_final[i + offset_y][j + offset_x] = alpha * img_final[i + offset_y][j + offset_x] + (1 - alpha) * \
                                                        img2[i][j]

    # Convert to grayscale
    gray = cv2.cvtColor(img_final, cv2.COLOR_BGR2GRAY)
    # Threshold to find non-black pixels
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Get bounding box
    x, y, w, h = cv2.boundingRect(contours[0])
    # Crop the image using the bounding box
    img_final = img_final[y:y + h, x:x + w]
    return img_final


def process_video(filename, callback, progress_callback):
    if not check_file(filename):
        callback("File check failed.", None)
        return

    cp = cv2.VideoCapture(filename)
    n_frames = int(cp.get(cv2.CAP_PROP_FRAME_COUNT))

    success, prev = cp.read()
    count = 0
    index = 0

    while success:
        progress = (index / n_frames) * 100
        progress_callback(progress, f"Processing frame: {index + 1}/{n_frames}")

        cp.set(cv2.CAP_PROP_POS_FRAMES, count)
        success, curr = cp.read()
        if not success:
            break

        # Stitching current frame with previous frame
        prev = stitch_images(prev, curr)
        index += 20
        count += 20
    cv2.imwrite("images/result.png", prev)
    callback("Finished processing.", "images/result.png")
    cp.release()
