import cv2 as cv

# 0 normalmente é a câmera padrão. Se abrir a câmera errada, trocar para 1 ou 2.
camera = cv.VideoCapture(0, cv.CAP_DSHOW)

if not camera.isOpened():
    raise RuntimeError("Não foi possível abrir a webcam. Deu merda em alguma coisa")
camera.set(cv.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv.CAP_PROP_FRAME_HEIGHT, 480)

try:
    while True:
        sucesso, imagem = camera.read()
        if not sucesso:
            print("Não foi possível capturar uma imagem.")
            break
        cv.imshow("Webcam - pressione Q para sair", imagem)
        if cv.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    camera.release()
    cv.destroyAllWindows()
