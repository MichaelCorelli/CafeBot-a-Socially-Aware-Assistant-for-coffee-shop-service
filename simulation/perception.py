import pybullet as p
import cv2
import numpy as np
from ultralytics import YOLO
from threading import Lock

class PerceptionModule:
    """
    YOLOv8-based 2D detection + 3D localization,
    with a thread-safe dynamic_semantic_map for navigation.
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
        
        self._map_lock = Lock()
        self.dynamic_semantic_map = []

    def get_camera_image(self, pepper, width=320, height=240):
      
        view_list = pepper.getCameraViewMatrix(2)
        proj_list = pepper.getCameraProjectionMatrix(2)
        _, _, rgba, depth_buf, _ = p.getCameraImage(
            width, height,
            viewMatrix=view_list,
            projectionMatrix=proj_list
        )
        if rgba is None:
            return None, None, None, None

        rgba = np.array(rgba, dtype=np.uint8).reshape((height, width, 4))
        image_bgr = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
        depth_buf = np.array(depth_buf, dtype=np.float32).reshape((height, width))

        view = np.array(view_list, dtype=np.float32).reshape((4,4), order='F')
        proj = np.array(proj_list, dtype=np.float32).reshape((4,4), order='F')

        return image_bgr, depth_buf, view, proj

    def detect_objects(self, image):
        
        if image is None:
            return []

        class_indices = [
            idx for idx, name in self.model.names.items()
            if name in self.target_classes
        ]
        results = self.model(image, classes=class_indices, verbose=False)
        
        detections = []
        for r in results:
            for box in r.boxes:
                coco_label = self.model.names[int(box.cls)]
                cafe_label = self.coco_to_cafe_map.get(coco_label)
                if cafe_label:
                    confidence = float(box.conf)
                    bbox = box.xyxy[0].cpu().numpy()
                    if confidence > 0.45:
                        detections.append({
                            "label": cafe_label,
                            "confidence": confidence,
                            "bbox": bbox
                        })
        return detections

    def localize_objects_3d(self, detections, depth_buffer, view_matrix, proj_matrix):
        
        inv_proj = np.linalg.inv(np.array(proj_matrix).reshape(4,4,order='F'))
        inv_view = np.linalg.inv(np.array(view_matrix).reshape(4,4,order='F'))
        height, width = depth_buffer.shape

        localized = []
        for det in detections:
            u = int((det['bbox'][0] + det['bbox'][2]) / 2)
            v = int((det['bbox'][1] + det['bbox'][3]) / 2)
            if not (0 <= u < width and 0 <= v < height):
                continue
            depth = depth_buffer[v, u]
            x_ndc =  2 * u / width  - 1
            y_ndc = -2 * v / height + 1
            z_ndc =  2 * depth    - 1
            clip = np.array([x_ndc, y_ndc, z_ndc, 1.0])
            eye = inv_proj @ clip
            eye /= eye[3]
            world_h = inv_view @ eye
            world = world_h[:3] / world_h[3]
            det['world_coordinates'] = world.tolist()
            localized.append(det)
        return localized

    def update_semantic_map(self, pepper, width=320, height=240):
        
        image, depth_buf, vm, pm = self.get_camera_image(pepper, width, height)
        if image is None:
            return
        det2d = self.detect_objects(image)
        det3d = self.localize_objects_3d(det2d, depth_buf, vm, pm)
        with self._map_lock:
            self.dynamic_semantic_map = [
                (d['label'], *d['world_coordinates']) for d in det3d
            ]

    def get_dynamic_semantic_map(self):
        
        with self._map_lock:
            return list(self.dynamic_semantic_map)
