import cv2

cap = cv2.VideoCapture(0)

print("Camera:", cap.isOpened())

ret, frame = cap.read()

print("Frame:", ret)

if ret:
    cv2.imwrite("teste_camera.jpg", frame)
    print("Imagem salva como teste_camera.jpg")

cap.release()