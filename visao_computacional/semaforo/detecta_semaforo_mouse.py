'''
Esse código NÃO MANDA COISA PRO MOTOR!!!! E MUITO MENOS DETECTA O SEMÁFORO SOZINHO! 

fiz ele só pra ver como que ficava as máscaras do semáforo e as cores! =) 

É só uns testes pra ver se tá detectando o semáforo e ajustar os valores do HSV! 

@author: Tibas =) + gustavão
'''
## Importando as bibliotecas
import cv2
import numpy as np

# Abre a webcam usando o sistema de captura do WINDOWSSSSSS! Se for no Ubunto acho que tem que mudar essa parte (abrir camera no linux é uma bosta).
camera = cv2.VideoCapture(0, cv2.CAP_DSHOW) # O índice 0 indica a câmera padrão. Tente 1 ou 2 se necessário.

# Faixas de cores no formato HSV:
# h = tonalidade, s = saturação e v = brilho. --> No OpenCV: h vai de 0 a 179; s e v vão de 0 a 255.
# Cada faixa contém um limite inferior e um superior.
# O vermelho usa duas faixas porque aparece nas duas extremidades de h.
# Estes valores são iniciais e precisam ser calibrados com a câmera.
faixas = {
    "vermelho": [
        ((0, 100, 150), (10, 255, 255)),
        ((170, 100, 150), (179, 255, 255)),
    ],
    "amarelo": [
        ((15, 100, 150), (38, 255, 255)),
    ],
    "verde": [
        ((40, 80, 150), (95, 255, 255)),
    ],
}

# Pelo menos 12% da região analisada deve ter a cor esperada.
min_fracao = 0.12

# A maior pontuação deve ser pelo menos 1,8 vez a segunda maior.
# Isso evita escolher uma cor quando o resultado está ambíguo.
min_dominancia = 1.8

# Exige a mesma classificação em quatro imagens consecutivas.
# O tempo necessário depende da velocidade de captura da câmera.
min_quadros = 4

# O bloco finally libera a câmera mesmo se ocorrer um erro.
try:
    if not camera.isOpened():
        raise RuntimeError("Não foi possível abrir a webcam.")

    # Captura algumas imagens para dar tempo à câmera de ajustar
    # automaticamente a exposição e o balanço de branco.
    for _ in range(30):
        sucesso, imagem = camera.read()

        if not sucesso:
            raise RuntimeError("Falha ao capturar imagem.")

    # Abre uma janela para selecionar o semáforo com o mouse.
    # Selecione apenas a caixa das três luzes, sem incluir o poste.
    # A ordem deve ser: vermelho em cima, amarelo no meio e verde embaixo.
    # Pressione Enter para confirmar.
    #
    # x e y: posição do canto superior esquerdo da seleção.
    # largura e altura: tamanho da seleção em pixels.
    x, y, largura, altura = map(int, cv2.selectROI(
        "Selecione as tres luzes", imagem, False, False
    ))
    cv2.destroyAllWindows()

    # Uma seleção cancelada tem tamanho zero.
    # Também rejeitamos regiões muito pequenas para esta configuração.
    if largura < 20 or altura < 60:
        raise RuntimeError("Seleção cancelada ou muito pequena.")

    # Guarda a classificação anterior e quantas vezes ela se repetiu.
    anterior = "indefinido"
    repeticoes = 0

    while True:
        # Lê uma nova imagem da webcam.
        sucesso, imagem = camera.read()

        if not sucesso:
            print("Captura interrompida: estado indefinido.")
            break

        # Guarda a pontuação de cada lâmpada na imagem atual.
        pontos = {}

        # Percorre as cores na ordem em que foram definidas em faixas.
        # O índice 0 corresponde ao vermelho, 1 ao amarelo e 2 ao verde.
        for indice, (cor, limites) in enumerate(faixas.items()):

            # Divide o semáforo em três partes verticais.
            # Dentro de cada parte, descarta as bordas para reduzir
            # a influência da carcaça e do fundo.
            x1 = x + int(largura * 0.15)
            x2 = x + int(largura * 0.85)
            y1 = y + int(altura * (indice + 0.15) / 3)
            y2 = y + int(altura * (indice + 0.85) / 3)

            # Recorta a região da lâmpada.
            # Em imagens NumPy, acessamos primeiro y e depois x.
            recorte = imagem[y1:y2, x1:x2]

            # Converte de BGR, formato usado pelo OpenCV, para HSV.
            hsv = cv2.cvtColor(recorte, cv2.COLOR_BGR2HSV)

            # Cria uma imagem preta do mesmo tamanho do recorte.
            # Ela será usada como máscara dos pixels aprovados.
            mascara = np.zeros(hsv.shape[:2], dtype=np.uint8)

            for inferior, superior in limites:
                # Pixels dentro da faixa ficam brancos (255).
                # Os demais ficam pretos (0).
                parcial = cv2.inRange(
                    hsv, np.array(inferior), np.array(superior)
                )

                # Une as faixas da mesma cor em uma única máscara.
                # Isso é necessário para as duas faixas de vermelho.
                mascara = cv2.bitwise_or(mascara, parcial)

            # Calcula a fração de pixels aprovados.
            # Exemplo: 0.25 significa que 25% da região passou no filtro.
            # Esse valor não é uma probabilidade de acerto.
            pontos[cor] = cv2.countNonZero(mascara) / mascara.size

        # Ordena as cores da maior pontuação para a menor.
        ranking = sorted(pontos, key=pontos.get, reverse=True)
        melhor, segunda = ranking[:2]

        # Só aceita a melhor cor se ela atingir o mínimo de pixels
        # e tiver uma vantagem suficiente sobre a segunda colocada.
        valido = (
            pontos[melhor] >= min_fracao
            and pontos[melhor]
            >= min_dominancia * max(pontos[segunda], 0.001)
        )

        detectado = melhor if valido else "indefinido"

        # Conta quantas imagens consecutivas tiveram o mesmo resultado.
        # Quando a classificação muda, a contagem recomeça em 1.
        if detectado == anterior:
            repeticoes += 1
        else:
            repeticoes = 1

        anterior = detectado

        # Só confirma a classificação após a quantidade mínima de imagens.
        # Enquanto isso, o estado permanece indefinido.
        if repeticoes >= min_quadros:
            estado = detectado
        else:
            estado = "indefinido"

        # Desenha a região selecionada na imagem.
        cv2.rectangle(
            imagem,
            (x, y),
            (x + largura, y + altura),
            (255, 255, 255),
            2,
        )

        # Escreve o estado confirmado na tela.
        cv2.putText(
            imagem,
            f"Semaforo: {estado}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )

        cv2.imshow("Detector - Q para sair", imagem)

        # Verifica o teclado. Pressione Q com a janela selecionada.
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    # Libera a webcam para outros programas e fecha as janelas.
    camera.release()
    cv2.destroyAllWindows()
