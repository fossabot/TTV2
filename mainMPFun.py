import mediapipe as mp
class faceDetector():
    def __init__(self):
        self.mp_face_mesh=mp.solutions.face_mesh
        self.face_mesh=self.mp_face_mesh.FaceMesh(max_num_faces=1,
                           refine_landmarks=True,
                           min_detection_confidence=0.5,
                           min_tracking_confidence=0.5)


    def findFace(self,img):
        results = self.face_mesh.process(img)
        return results


