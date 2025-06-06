import pybullet as p
import cv2
import numpy as np
from ultralytics import YOLO

class PerceptionModule:
    """
    YOLOv8 pre-trained model for object detection in a simulated environment.
    """
    def __init__(self):
        self.model = YOLO('yolov8n.pt')
        print("PerceptionModule initialized with pre-trained YOLOv8 model.")

        self.coco_to_cafe_map = {
            'cup': 'cappuccino',
            'bottle': 'water_bottle',
            'dining table': 'table',
            'chair': 'chair',
            'sandwich': 'sandwich',
            'cake': 'muffin',
            'donut': 'cornetto'
        }
        self.target_classes = list(self.coco_to_cafe_map.keys())

    def get_camera_image(self, pepper, width=320, height=240):
    
        view_matrix = pepper.getCameraViewMatrix(2)
        proj_matrix = pepper.getCameraProjectionMatrix(2)
        
        _, _, rgba_img, _, _ = p.getCameraImage(width, height, viewMatrix=view_matrix, projectionMatrix=proj_matrix)
        
        if rgba_img is None:
            return None
        
        image_rgba = np.array(rgba_img, dtype=np.uint8).reshape((height, width, 4))
        image_bgr = cv2.cvtColor(image_rgba, cv2.COLOR_RGBA2BGR)
        return image_bgr

    def detect_objects(self, image):
        if image is None:
            return []
    
        class_indices = [list(self.model.names.values()).index(c) for c in self.target_classes if c in self.model.names.values()]
        
        results = self.model(image, classes=class_indices, verbose=False)
        
        detections = []
        for result in results:
            for box in result.boxes:
                coco_label = self.model.names[int(box.cls)]
                
                if coco_label in self.coco_to_cafe_map:
                    cafe_label = self.coco_to_cafe_map[coco_label]
                    confidence = float(box.conf)
                    bbox = box.xyxy[0].cpu().numpy()
                    
                    if confidence > 0.45:
                        detections.append({
                            "label": cafe_label,
                            "confidence": confidence,
                            "bbox": bbox
                        })
        return detections

    def localize_objects_3d(self, pepper, detections, width=320, height=240):
        if not detections:
            return []

        view_matrix = np.array(pepper.getCameraViewMatrix(2)).reshape(4, 4, order='F')
        proj_matrix = np.array(pepper.getCameraProjectionMatrix(2)).reshape(4, 4, order='F')
        
        _, _, _, depth_buffer, _ = p.getCameraImage(width, height, viewMatrix=view_matrix.T, projectionMatrix=proj_matrix.T)

        inv_proj_matrix = np.linalg.inv(proj_matrix)
        inv_view_matrix = np.linalg.inv(view_matrix)

        localized_objects = []
        for det in detections:
            bbox = det['bbox']
            u = int((bbox[0] + bbox[2]) / 2)
            v = int((bbox[1] + bbox[3]) / 2)

            if 0 <= u < width and 0 <= v < height:
                depth = depth_buffer[v, u]
                
                if depth < 1.0:
                    x = (2 * u / width - 1)
                    y = -(2 * v / height - 1)
                    
                    pos_clip = (x, y, (2 * depth - 1), 1.0)
                    pos_eye = np.dot(inv_proj_matrix, pos_clip)
                    pos_world_homogeneous = np.dot(inv_view_matrix, pos_eye)
                    
                    if pos_world_homogeneous[3] != 0:
                        pos_world = pos_world_homogeneous[:3] / pos_world_homogeneous[3]
                        det['world_coordinates'] = pos_world.tolist()
                        localized_objects.append(det)

        return localized_objects