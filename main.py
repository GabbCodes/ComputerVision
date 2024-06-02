import math
import random
import cvzone
import cv2
import numpy as np
from cvzone.HandTrackingModule import HandDetector

# Inicialização da captura de vídeo
cap = cv2.VideoCapture(2)  # Abre a câmera 2 (pode ser necessário ajustar o índice)
cap.set(3, 1280)  # Define a largura do vídeo para 1280 pixels
cap.set(4, 720)  # Define a altura do vídeo para 720 pixels

# Inicialização do detector de mãos
detector = HandDetector(detectionCon=0.9, maxHands=1)  # Detecta uma mão com confiança de 90%

class SnakeGameClass:
    def __init__(self, pathFood):
        # Inicialização dos pontos da cobra (lista vazia no início)
        self.points = []
        self.lengths = []  # Comprimentos dos segmentos da cobra
        self.currentLength = 0  # Comprimento total atual da cobra
        self.allowedLength = 150  # Comprimento máximo permitido antes de comer
        self.previousHead = 0, 0  # Posição anterior da cabeça da cobra

        # Carrega a imagem da comida
        self.imgFood = cv2.imread(pathFood, cv2.IMREAD_UNCHANGED)
        self.hFood, self.wFood, _ = self.imgFood.shape  # Obtém as dimensões da imagem da comida
        self.foodPoint = 0, 0  # Posição inicial da comida
        self.randomFoodLocation()  # Gera uma posição aleatória para a comida

        self.score = 0  # Pontuação inicial
        self.gameOver = False  # Estado do jogo (False = em andamento)

    def randomFoodLocation(self):
        # Gera uma posição aleatória para a comida dentro dos limites da tela
        self.foodPoint = random.randint(100, 1000), random.randint(100, 600)

    def update(self, imgMain, currentHead):
        # Lógica principal do jogo, atualizada a cada quadro

        if self.gameOver:
            # Se o jogo acabou, exibe a mensagem "Game Over" e a pontuação
            cvzone.putTextRect(imgMain, "Fim de jogo", [300, 400],
                               scale=2, thickness=5, offset=20)
            cvzone.putTextRect(imgMain, f'Seus pontos: {self.score}', [300, 550],
                               scale=2, thickness=5, offset=20)
        else:
            # Se o jogo está em andamento:
            px, py = self.previousHead  # Coordenadas da cabeça anterior
            cx, cy = currentHead  # Coordenadas da cabeça atual

            self.points.append([cx, cy])  # Adiciona a nova posição da cabeça à lista de pontos
            distance = math.hypot(cx - px, cy - py)  # Calcula a distância entre as cabeças
            self.lengths.append(distance)  # Adiciona o comprimento do novo segmento
            self.currentLength += distance  # Atualiza o comprimento total da cobra
            self.previousHead = cx, cy  # Atualiza a posição da cabeça anterior

            # Reduz o comprimento da cobra se exceder o limite
            if self.currentLength > self.allowedLength:
                for i, length in enumerate(self.lengths):
                    self.currentLength -= length
                    self.lengths.pop(i)
                    self.points.pop(i)
                    if self.currentLength < self.allowedLength:
                        break

            # Verifica se a cobra comeu a comida
            rx, ry = self.foodPoint
            if rx - self.wFood // 2 < cx < rx + self.wFood // 2 and \
                    ry - self.hFood // 2 < cy < ry + self.hFood // 2:
                self.randomFoodLocation()  # Gera nova posição para a comida
                self.allowedLength += 50  # Aumenta o comprimento permitido
                self.score += 1  # Incrementa a pontuação
                print(self.score)

            # Desenha a cobra na imagem
            if self.points:
                for i, point in enumerate(self.points):
                    if i != 0:
                        cv2.line(imgMain, self.points[i - 1], self.points[i], (0, 255, 0), 20)
                cv2.circle(imgMain, self.points[-1], 20, (0, 255, 0), cv2.FILLED)  # Desenha a cabeça

            # Desenha a comida na imagem
            imgMain = cvzone.overlayPNG(imgMain, self.imgFood,
                                        (rx - self.wFood // 2, ry - self.hFood // 2))

            # Exibe a pontuação na imagem
            cvzone.putTextRect(imgMain, f'Pontos: {self.score}', [50, 80],
                               scale=2, thickness=3, offset=10)

            # Verifica colisão da cobra com o próprio corpo
            pts = np.array(self.points[:-2], np.int32)  # Converte os pontos em um array NumPy
            pts = pts.reshape((-1, 1, 2))  # Formata o array para ser usado na função pointPolygonTest
            cv2.polylines(imgMain, [pts], False, (0, 255, 0), 3)  # Desenha a linha da cobra (opcional)
            minDist = cv2.pointPolygonTest(pts, (cx, cy), True)  # Calcula a distância mínima entre a cabeça e o corpo

            if -1 <= minDist <= 1:  # Se a distância for pequena, houve colisão
                print("Colidiu")
                self.gameOver = True  # Termina o jogo
                self.points = []  # Reinicia os pontos da cobra
                self.lengths = []  # Reinicia os comprimentos dos segmentos
                self.currentLength = 0  # Reinicia o comprimento total
                self.allowedLength = 150  # Reinicia o comprimento permitido
                self.previousHead = 0, 0  # Reinicia a posição da cabeça anterior
                self.randomFoodLocation()  # Gera nova posição para a comida

        return imgMain  # Retorna a imagem com as atualizações


# Cria uma instância do jogo com a imagem "Apple.png" como comida
game = SnakeGameClass("Apple.png")

# Loop principal do jogo
while True:
    success, img = cap.read()  # Lê um quadro da câmera
    img = cv2.flip(img, 1)  # Inverte a imagem horizontalmente (efeito espelho)
    hands, img = detector.findHands(img, flipType=False)  # Detecta as mãos na imagem

    if hands:
        lmList = hands[0]['lmList']  # Obtém a lista de pontos de referência da mão
        pointIndex = lmList[8][0:2]  # Obtém as coordenadas (x, y) da ponta do dedo indicador
        img = game.update(img, pointIndex)  # Atualiza o jogo com a posição do dedo

    cv2.imshow("Image", img)  # Exibe a imagem resultante
    key = cv2.waitKey(1)  # Aguarda por 1 milissegundo por uma tecla pressionada
    if key == ord('r'):  # Se a tecla 'r' for pressionada, reinicia o jogo
        game.gameOver = False
